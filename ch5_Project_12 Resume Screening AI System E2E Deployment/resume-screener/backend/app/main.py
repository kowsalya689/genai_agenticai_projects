import logging
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import DEFAULT_MODEL, FRONTEND_DIST, MAX_FILE_MB, MAX_FILES, SAMPLE_DIR
from .embedder import MODELS, st_available
from .parsing import extract_text
from .pipeline import run_screening

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Resume Screener", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "default_model": DEFAULT_MODEL, "sentence_transformers": st_available()}


@app.get("/api/models")
def models():
    st = st_available()
    return {
        "default": DEFAULT_MODEL,
        "models": [{"key": k, "label": v["label"], "size": v["size"], "note": v["note"],
                    "available": st or k == "hashing"} for k, v in MODELS.items()],
    }


def _sample_resumes():
    return sorted(p for p in (SAMPLE_DIR / "Resumes").glob("*") if p.suffix.lower() in {".pdf", ".docx", ".txt"})


@app.get("/api/samples")
def samples():
    jds = []
    for p in sorted((SAMPLE_DIR / "JD").glob("*.txt")):
        label = p.stem.replace("_", " ")
        jds.append({"id": p.name, "label": label, "text": p.read_text(encoding="utf-8", errors="ignore")})
    return {"jds": jds, "resumes": [p.name for p in _sample_resumes()]}


@app.post("/api/screen")
def screen(
    jd_text: str = Form(""),
    jd_file: Optional[UploadFile] = File(None),
    resumes: List[UploadFile] = File(default=[]),
    use_sample_resumes: bool = Form(False),
    top_k: int = Form(5),
    model: str = Form(DEFAULT_MODEL),
):
    jd = jd_text.strip()
    if not jd and jd_file is not None and jd_file.filename:
        try:
            jd = extract_text(jd_file.filename, jd_file.file.read())
        except ValueError as e:
            raise HTTPException(422, f"Job description: {e}")
    if len(jd.split()) < 15:
        raise HTTPException(422, "Add a job description of at least a few sentences.")

    files: list[tuple[str, bytes]] = []
    for f in resumes:
        data = f.file.read()
        if len(data) > MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(413, f"{f.filename} is larger than {MAX_FILE_MB} MB.")
        files.append((f.filename or "resume", data))
    if use_sample_resumes:
        files.extend((p.name, p.read_bytes()) for p in _sample_resumes())
    if not files:
        raise HTTPException(422, "Add at least one resume.")
    if len(files) > MAX_FILES:
        raise HTTPException(413, f"Too many resumes (max {MAX_FILES}).")

    top_k = max(1, min(top_k, len(files)))
    return run_screening(jd, files, top_k, model)


# Serve the built frontend (npm run build) from the same server.
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = FRONTEND_DIST / path
        return FileResponse(f if path and f.is_file() else FRONTEND_DIST / "index.html")
