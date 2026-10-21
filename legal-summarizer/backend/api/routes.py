from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from backend.api.deps import get_app_settings, get_summarizer
from backend.config import Settings
from backend.core.errors import AppError
from backend.schemas import (ExtractResponse, HealthResponse, ModelInfo, Sample, SummarizeRequest, SummarizeResponse)
from backend.services.extract import extract_text
from backend.services.samples import load_samples

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request, settings: Settings = Depends(get_app_settings)):
    s = request.app.state.summarizer
    loaded = s.is_loaded
    err = getattr(s, "load_error", None)
    return HealthResponse(status="ok" if loaded else ("error" if err else "loading"), model_loaded=loaded,
                          model_error=err, device=getattr(s, "device", None), version=settings.version)


@router.get("/model", response_model=ModelInfo, tags=["system"])
def model_info(request: Request):
    return ModelInfo(**request.app.state.summarizer.info())


@router.get("/samples", response_model=list[Sample], tags=["demo"])
def samples():
    return load_samples()


@router.post("/extract", response_model=ExtractResponse, tags=["summarise"])
async def extract(file: UploadFile = File(...), settings: Settings = Depends(get_app_settings)):
    """Upload .txt / .md / .pdf / .docx and get the plain text back (to review before summarising)."""
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise AppError(413, "file_too_large", f"File exceeds the {settings.max_upload_mb} MB limit.")
    text = await run_in_threadpool(extract_text, file.filename or "", data)
    if len(text) > settings.max_chars:
        raise AppError(413, "document_too_long", f"Document exceeds {settings.max_chars:,} characters.")
    return ExtractResponse(filename=file.filename or "upload", characters=len(text), text=text)


@router.post("/summarize", response_model=SummarizeResponse, tags=["summarise"])
def summarize(body: SummarizeRequest, summarizer=Depends(get_summarizer), settings: Settings = Depends(get_app_settings)):
    """Summarise one legal document. (Sync endpoint -> FastAPI runs it in a worker thread, so the server stays responsive.)"""
    if len(body.text) > settings.max_chars:
        raise AppError(413, "document_too_long", f"Document exceeds {settings.max_chars:,} characters.")
    try:
        result = summarizer.summarize(body.text, body.compression, body.max_summary_tokens, body.num_beams)
    except ValueError as exc:
        raise AppError(422, "invalid_document", str(exc)) from exc
    return result
