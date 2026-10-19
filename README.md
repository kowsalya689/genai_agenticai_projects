# Next Word Prediction System — Web Application

A production-style web application that serves **trained next-word
prediction models** (TensorFlow / Keras) over a REST API with a Bootstrap
frontend. Three recurrent architectures — **SimpleRNN, GRU, and LSTM** — are
trained on the same corpus with identical preprocessing and can be selected
per request; a comparison table (accuracy / perplexity / params / speed) is
produced by the training script. An optional DistilGPT2 script
(`notebooks/distilgpt2_compare.py`) provides a modern-transformer reference
point. It converts the experimentation notebook (`NX-NLP-2026-014`) into a
modular, deployable service.

The app **does not retrain** anything — it loads the existing trained
`.keras` model and pickled tokenizer and reproduces the notebook's
preprocessing, top-k prediction, and temperature-sampling logic exactly.

---

## Features

- Enter a sentence/phrase and **predict the next word**
- **Switch between LSTM / GRU / SimpleRNN** per request (UI dropdown or
  `"model"` field in the API); `GET /models` lists what's available
- **Top-k predictions** with probabilities (k = 3 / 5 / 10)
- **Multi-word text generation** from a seed
- Adjustable **temperature** (0 = greedy, higher = more creative)
- REST API with automatic **OpenAPI docs** at `/docs`
- Bootstrap single-page UI
- Dockerfile + Render/Railway configs for deployment
- Test suite that runs **without TensorFlow** (fakes) plus real-artifact readiness

---

## Project layout

```
next_word_predictor/
├── app/
│   ├── main.py              # FastAPI entrypoint (app instance)
│   ├── routes/              # /predict, /generate, /health
│   ├── services/            # predictor.py (predict_next_word, generate_text)
│   ├── models/              # model_loader, tokenizer_loader, schemas
│   ├── utils/               # text_cleaner, text_normalizer
│   └── config/              # settings.py
├── static/                  # css/, js/
├── templates/               # index.html
├── notebooks/               # export_artifacts.py (save model/tokenizer/config)
├── saved_models/            # <- put .keras + tokenizer.pkl + config.json here
├── data/                    # optional Articles.csv sample
├── tests/                   # pytest suite
├── requirements.txt
├── Dockerfile / Procfile / render.yaml
└── README.md
```

> **Naming note.** Python cannot have both a top-level `app.py` module and an
> `app/` package (the package shadows the module). The runnable entrypoint
> therefore lives at **`app/main.py`**, launched with `uvicorn app.main:app`.

---

## 1. Installation

```bash
# clone / unzip, then:
cd next_word_predictor

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

> **Trained models are already bundled** in `saved_models/` (LSTM, GRU, RNN +
> tokenizer/config). You do **not** need to train anything — go straight to
> section 2 to run the app.

> ⚠️ **Keras version matters.** The `.keras` artifacts were exported with
> **Keras 3.13.2**. `requirements.txt` therefore pins both `tensorflow==2.16.1`
> **and** `keras==3.13.2`. Installing TensorFlow alone pulls Keras 3.0.5, which
> **cannot** read these artifacts and produces the "model not loaded" error.
> Always install via `pip install -r requirements.txt`.

### Train the models

```bash
python notebooks/train_models.py --data Articles.csv --out saved_models
```

This trains all three architectures and writes everything the app needs:

| File | Purpose |
|------|---------|
| `next_word_lstm_best.keras` | LSTM model (default) |
| `next_word_gru_best.keras` | GRU model |
| `next_word_rnn_best.keras` | SimpleRNN baseline |
| `tokenizer.pkl` | fitted tokenizer, shared by all three |
| `config.json` | context length + hyperparameters |
| `comparison.json` / `.csv` | metrics table for the video |
| `training_curves.png` | validation loss/accuracy curves |

The app serves whichever architectures it finds on disk — a single LSTM
artifact still works exactly as before.

Use `notebooks/export_artifacts.py` — paste its block into your notebook after
training to produce all three files.

---

## 2. Run locally

```bash
uvicorn app.main:app --reload
# or
python app/main.py
```

- UI: <http://localhost:8000/>
- Interactive API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

---

## 3. API guide

### `POST /predict`
Predict the top-k next words.

**Request**
```json
{ "text": "the stock market", "top_k": 5 }
```
**Response**
```json
{
  "input": "the stock market",
  "predictions": [
    { "word": "rose", "probability": 0.41 },
    { "word": "fell", "probability": 0.22 }
  ]
}
```

### `POST /generate`
Generate a multi-word continuation.

**Request**
```json
{ "text": "the government has decided to", "num_words": 14, "temperature": 0.7 }
```
**Response**
```json
{
  "input": "the government has decided to",
  "generated_text": "the government has decided to raise fuel prices ...",
  "num_words": 14,
  "temperature": 0.7
}
```

### `GET /health`
```json
{ "status": "ok", "model_loaded": true, "context_length": 15, "vocab_size": 5001 }
```

**curl example**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"the stock market","top_k":5}'
```

Validation is automatic: empty/whitespace text, `top_k` out of `[1,20]`,
`num_words` out of `[1,50]`, or `temperature` out of `[0,2]` return `422`.

---

## 4. Model artifacts

- **Save model:** `model.save("saved_models/next_word_lstm_best.keras")`
  (or let `ModelCheckpoint` write it during training).
- **Save tokenizer:** `pickle.dump(tokenizer, open("saved_models/tokenizer.pkl","wb"))`.
- **Save vocabulary:** the vocabulary lives inside the tokenizer
  (`word_index` / `index_word`), so persisting the tokenizer persists the vocab.
- **Save config:** `config.json` stores `context_length` so preprocessing is
  reproduced exactly (if absent, it is inferred from the model's input shape).
- **Load:** all three are loaded once at startup and cached
  (`app/models/model_loader.py`).

---

## 5. Testing

```bash
pytest
```

The suite runs **without TensorFlow or real artifacts** by injecting fake
model/tokenizer objects: preprocessing, predictor logic (top-k ordering, greedy
determinism, OOV stop, seeded sampling), API responses, and input validation.

---

## 6. Deployment

### Docker (local or any host)
```bash
docker build -t next-word-predictor .
docker run -p 8000:8000 next-word-predictor
```
The image reads `$PORT` if set (defaults to 8000).

### Render
Push to a Git repo and create a **Web Service** (uses `render.yaml`), or set:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Railway
Railway detects the `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Add the artifacts to `saved_models/` (or mount a volume / object storage).

### Notes for all hosts
- TensorFlow images are large; prefer a plan with adequate memory.
- Model + tokenizer are loaded once at startup (cached singleton).
- Configure paths via `MODEL_PATH`, `TOKENIZER_PATH`, `CONFIG_PATH` env vars.

---

## Why FastAPI (vs Flask)?

See `docs/ARCHITECTURE_REVIEW.md`. In short: built-in Pydantic validation
(the assessment requires input validation), automatic OpenAPI docs, async I/O,
and first-class typing make FastAPI the better fit here. A Flask port is
straightforward if required (swap the router layer; the service/model/utils
modules are framework-agnostic).
