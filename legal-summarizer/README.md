# LexBrief: Legal Document Summarizer

FastAPI backend + web UI around the fine-tuned BART model from `notebooks/legal_summarization_bart.ipynb`
(Synthra AI assessment SA-NLP-2026-014). Paste or upload a contract, get a summary in which every number,
date and name is checked against the source.

## 1. Project structure

```
legal-summarizer/
├── run.py                      start the app
├── requirements.txt            runtime dependencies
├── requirements-dev.txt        + pytest, httpx
├── .env.example                all settings (copy to .env)
├── Dockerfile
├── backend/
│   ├── main.py                 app factory: middleware, error handlers, serves the frontend
│   ├── config.py               settings (env / .env)
│   ├── schemas.py              request and response models
│   ├── api/
│   │   ├── routes.py           /api/v1 endpoints
│   │   └── deps.py             dependencies (settings, model-ready check)
│   ├── core/
│   │   ├── middleware.py       request id + timing, security headers, rate limit
│   │   ├── errors.py           one JSON error shape
│   │   └── logging.py
│   ├── services/
│   │   ├── summarizer.py       model loading + full pipeline (chunk, generate, merge, check)
│   │   ├── text_utils.py       cleaning + legal-aware sentence splitter
│   │   ├── chunking.py         overlapping chunks for long documents
│   │   ├── faithfulness.py     flags numbers/dates/names not in the source
│   │   ├── extract.py          .txt .md .pdf .docx to text
│   │   └── samples.py
│   └── data/samples.json       the four sample documents from the notebook
├── frontend/                   index.html, css/styles.css, js/{app,api,highlight,config}.js
├── model/                      put bart_legal_final/ here (see model/README.md)
├── notebooks/                  your original notebook
├── scripts/                    setup.sh, setup.bat
└── tests/                      18 tests (no GPU or model needed)
```

## 2. Install and run

Requires Python 3.10 to 3.12.

**Windows**
```bat
cd legal-summarizer
scripts\setup.bat
.venv\Scripts\activate
python run.py
```

**Linux / macOS**
```bash
cd legal-summarizer
bash scripts/setup.sh            # add "gpu" for a CUDA build of torch:  bash scripts/setup.sh gpu
source .venv/bin/activate
python run.py
```

Manual install (what the scripts do):
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu     # CPU build, much smaller
pip install -r requirements.txt
cp .env.example .env                                                    # Windows: copy .env.example .env
python run.py
```

Open **http://127.0.0.1:8000** for the UI and **http://127.0.0.1:8000/docs** for the interactive API docs.
The status pill in the UI turns green when the model has loaded.

**Model:** unzip `bart_legal_final.zip` (downloaded by the notebook, section 14) into `model/bart_legal_final/`.
Without it the app downloads `facebook/bart-large-cnn` on first start. If you trained with transformers 5.x
and loading fails, run `pip install -U transformers`.

## 3. Run the tests
```bash
pytest -q
```

## 4. API

Base path `/api/v1`. All errors share one shape: `{"error": {"code", "message", "request_id"}}`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | `status` is `loading`, `ok` or `error` |
| GET | `/model` | model size, layers, heads, device, pipeline defaults |
| GET | `/samples` | sample documents from the notebook |
| POST | `/extract` | multipart upload (`file`), returns plain text from .txt/.md/.pdf/.docx |
| POST | `/summarize` | summarise one document |

```bash
curl -X POST http://127.0.0.1:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "This Agreement is effective as of 1 July 2026 between Acme Ltd and Beta Pvt Ltd ...", "compression": 0.2}'
```

Request fields: `text` (required), `compression` (0.05 to 0.6, default 0.20), `max_summary_tokens` (default 350), `num_beams` (default 4).
Response: `summary`, token and word counts, `compression_ratio`, `passes`, `warnings`, `faithfulness` (unsupported numbers/dates/terms), `model`, `elapsed_ms`.

Any client can call this API (a Flutter or mobile app only needs these same JSON endpoints).

## 5. Header handling

| Header | Where | What it does |
|---|---|---|
| `X-Request-ID` | request and response | traced through logs and error bodies; a safe client-supplied value is kept |
| `X-Process-Time-Ms` | response | server time per request |
| `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` | response | security hardening (CSP is relaxed only on `/docs`) |
| `Cache-Control: no-store` | `/api/*` responses | legal text is never cached |
| `Strict-Transport-Security` | response in production | enabled when `ENVIRONMENT=production` |
| `Access-Control-*` | CORS | only origins in `ALLOWED_ORIGINS` |
| `X-RateLimit-Limit/Remaining`, `Retry-After` | `/summarize`, `/extract` | per-IP limit, 429 when exceeded |
| `Content-Encoding: gzip` | large responses | compression |

## 6. How it maps to the assessment

The pipeline in `backend/services/summarizer.py` is the notebook's section 8 (clean, sentence split, chunk with overlap,
BART per chunk with a length budget, merge and dedupe, summarise again if still long, faithfulness check). Compression target
is about 20%, capped at 350 tokens. For the mandatory video, the notebook's section 13 dry run covers tokenisation,
attention/encoding, decoding and post-processing, and this app is the working system to demo alongside it.

## 7. Configuration

All settings are in `.env.example`. Common ones: `MODEL_DIR`, `DEVICE`, `ALLOWED_ORIGINS`, `RATE_LIMIT_PER_MINUTE`, `ENVIRONMENT`.

## 8. Troubleshooting

* **Status pill stays on "Loading the model"**: first start loads about 1.6 GB; watch the terminal. CPU summarisation of a long contract can take a few minutes.
* **"Cannot reach the server"**: the app is not running, or the frontend is on another origin that is not in `ALLOWED_ORIGINS`.
* **Out of memory on GPU**: set `DEVICE=cpu`, or lower `NUM_BEAMS`.
* **PDF gives "No text could be extracted"**: it is a scan; run OCR first.
* **Production**: `ENVIRONMENT=production` and run `uvicorn backend.main:app --host 0.0.0.0 --port 8000` (or use the Dockerfile) behind HTTPS. The rate limiter is in memory, so use one worker or move it to Redis for more.
* **Always have a person review legal summaries.** The checker cannot detect a changed obligation such as may versus shall.
