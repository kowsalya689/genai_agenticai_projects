# Multilingual Support Translator

A simple full-stack language-translation web app. A **Flask** backend serves a
**vanilla HTML/CSS/JS** frontend and runs Meta's pretrained multilingual Transformer
**`facebook/nllb-200-distilled-600M`** (No Language Left Behind) for inference.

It auto-detects the source language, translates into any supported target, and preserves
non-translatable tokens such as **error codes, URLs, emails, and product IDs**.

## Features

- Auto source-language detection (or pick manually)
- 10 languages out of the box: English, French, Spanish, German, Hindi, Tamil, Telugu,
  Arabic, Chinese, Portuguese (extend `LANGUAGES` in `translator.py` for more — NLLB
  supports 200)
- Term protection so `ERR-500`, `SKU-99A`, URLs, and emails come through unchanged
- Swap languages, copy output, character counter, `Ctrl/Cmd+Enter` to translate
- Clean, responsive single-page UI

## Project structure

```
translation_app/
├── app.py              # Flask server + JSON API
├── translator.py       # NLLB pipeline: detect -> protect -> translate -> restore
├── requirements.txt
├── templates/
│   └── index.html      # frontend markup
└── static/
    ├── style.css       # styling
    └── app.js          # frontend logic (calls the API)
```

## Setup & run

Requires **Python 3.9+**. A GPU is optional (it will use CPU automatically, just slower).

```bash
cd translation_app
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

> **First translation is slow:** the model (~2.5 GB) downloads from the Hugging Face Hub
> and loads into memory on the first `/api/translate` call. Later requests are fast.

## API

| Method | Endpoint         | Body / Notes                                         |
|--------|------------------|------------------------------------------------------|
| GET    | `/api/languages` | List of `{iso, name}` supported languages            |
| GET    | `/api/health`    | `{status, model_loaded}`                             |
| POST   | `/api/translate` | `{ "text": "...", "target": "hi", "source": "auto" }`|

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "My payment failed with error ERR-500.", "target": "hi"}'
```

Response:

```json
{
  "translation": "मेरा भुगतान ERR-500 त्रुटि के साथ विफल हो गया।",
  "src_iso": "en", "src_name": "English",
  "tgt_iso": "hi", "tgt_name": "Hindi",
  "confidence": 1.0, "latency_ms": 812.4
}
```

## Notes

- The model runs locally — no data leaves your machine.
- For production you would put this behind a WSGI server (e.g. `gunicorn`/`waitress`)
  and add rate limiting; the built-in Flask server is for local/demo use.
