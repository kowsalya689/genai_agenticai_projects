"""Flask backend for the multilingual customer-support translation app.

Routes
------
GET  /                -> serves the single-page frontend
GET  /api/languages   -> list of supported languages (for the dropdowns)
GET  /api/health      -> readiness probe (reports whether the model is loaded)
POST /api/translate   -> {text, target, source?} -> {translation, ...}

Run:  python app.py     (then open http://127.0.0.1:5000)
The NLLB model loads lazily on the first /api/translate call.
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, render_template, request

from translator import LANGUAGES, Translator

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("app")

app = Flask(__name__)


@app.get("/")
def index():
    "Serve the frontend."
    return render_template("index.html")


@app.get("/api/languages")
def languages():
    "Return supported languages as an ordered list for the UI dropdowns."
    return jsonify([
        {"iso": iso, "name": meta["name"]} for iso, meta in LANGUAGES.items()
    ])


@app.get("/api/health")
def health():
    "Lightweight readiness probe."
    return jsonify({"status": "ok", "model_loaded": Translator._instance is not None})


@app.post("/api/translate")
def translate():
    "Translate a message. Body: {text, target, source?}."
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    target = (data.get("target") or "").strip()
    source = (data.get("source") or "auto").strip()

    if not text:
        return jsonify({"error": "Please enter some text to translate."}), 400
    if target not in LANGUAGES:
        return jsonify({"error": f"Unsupported target language '{target}'."}), 400

    try:
        result = Translator.get().translate(text, tgt_iso=target, src_iso=source)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("Translation failed")
        return jsonify({"error": f"Translation failed: {exc}"}), 500


if __name__ == "__main__":
    # threaded=False keeps a single worker so the ~2.5 GB model loads only once.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=False)
