# Shortlist – resume screening web app

Upload a job description and resumes (PDF, DOCX, TXT). The app ranks the resumes by meaning (sentence embeddings),
gives each a fit score and a reason, and extracts name, email, phone, LinkedIn and GitHub into a table.
It implements the workflow from your notebook and notes, as a FastAPI backend and a React frontend.

## Run it

You need Python 3.10+ and, only if you want to edit the UI, Node 18+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
Open http://localhost:8000. The built UI is already in `frontend/dist`.
(`start.sh` / `start.bat` run the last command for you.)

First run with the default model (BGE-large, 1.3 GB) downloads it once. For a quick start pick
**BGE Small** in the UI, or set `EMBED_MODEL=bge-small` before starting the server.

Develop the UI with hot reload:
```bash
cd frontend && npm install && npm run dev      # http://localhost:5173, proxies /api to :8000
npm run build                                  # rebuild frontend/dist
```
Tests: `cd backend && pip install pytest && python -m pytest -q`

## How it maps to your notebook

| Notebook task | Code |
|---|---|
| 1 Read PDF/DOCX/TXT | `backend/app/parsing.py` |
| 3 Preprocess JD and resumes | `preprocess.py` |
| 4 / 5 Split resume / JD into sections (with fallback) | `sections.py` |
| 6 Chunk + embed (BGE) | `embedder.py`, `sections.chunk_items` |
| 7 Section-by-section comparison + evidence | `pipeline.compare_section` |
| 8 Weighted score with years-of-experience check | `pipeline.run_screening`, weights in `config.py` |
| 9 Rank, shortlist top K | `pipeline.run_screening` |
| 10 Contact extraction (regex) + NER | `extract.py` |

## Scoring

Each resume gets a 0–100 **fit score**:
semantic match to required skills (30%), responsibilities (15%), nice-to-have (5%), role summary (5%),
must-have skill coverage (25%), nice-to-have coverage (5%), years of experience (15%).
Sections the JD does not have are dropped and the other weights are rescaled.

Cosine similarities from embedding models sit in a narrow band, so each model has a calibration range in
`embedder.py` (`lo`/`hi`) that maps similarity to 0–1. The fit score is therefore an absolute measure;
the API also returns `relative_score` (min-max within the batch, as in your notebook).
The calibration ranges for models other than BGE-large are estimates – check them on your own data.

## Spec checklist (assessment PDF)

- 4.1 PDF/DOCX/TXT ingestion – yes.
- 4.2 Same cleaning for JD and resumes – lowercasing, tokenising, stopword removal. Stopwords are only removed for token features (offline embedder); transformer embeddings get the lowercased text with function words kept.
- 4.3 Skills, years, designation, contacts extracted – yes (skills via an alias taxonomy in `skills.py`).
- 4.4 Sentence embeddings – BGE and others.
- 4.5 Variants and unseen terms – alias normalisation (JS = JavaScript, PySpark = Spark) plus a subword hashing embedder.
- 4.6 Cosine ranking – yes.
- 4.7 Explainability – reason, matched and missing skills, JD-vs-resume evidence passages.
- 4.8 Fairness – the resume header (name, contacts) is excluded from scoring; **Blind review** hides names and contacts in the UI.
- 4.9 Shortlist size – the "Shortlist size" control.

## Limits worth knowing

- Scanned (image-only) PDFs have no text and are reported as unreadable; add OCR if you need them.
- The optional NER model (`yashpwr/resume-ner-bert`) only adds the designation when the header heuristic finds none. Set `USE_NER=0` to skip it.
- If the chosen model cannot be loaded, the app falls back to a built-in offline embedder and says so in a banner.
- The skill taxonomy covers data, BI, ML and common software skills. Extend `TAXONOMY` in `skills.py` for other roles.

## API

`POST /api/screen` (multipart): `jd_text` or `jd_file`, `resumes` (files), `use_sample_resumes`, `top_k`, `model`.
Also `GET /api/models`, `GET /api/samples`, `GET /api/health`. Interactive docs at `/docs`.
