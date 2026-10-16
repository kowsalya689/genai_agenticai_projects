<<<<<<< HEAD
# Acme Retail – Product Recommendation Similarity System

FastAPI web app + FastText embeddings + cosine similarity (Assessment AR-ML-2026-006).

## Project layout
```
acme_recommender/
├── app/
│   ├── main.py              # FastAPI app, start-up (loads model once), serves the UI
│   ├── config.py            # paths + FastText hyper-parameters
│   ├── schemas.py           # Pydantic request/response models
│   ├── api/routes.py        # REST endpoints
│   ├── core/
│   │   ├── text_processing.py   # clean -> stop-words
│   │   ├── data_loader.py       # CSV -> prepared DataFrame
│   │   ├── embeddings.py        # FastText train/load + text -> vector
│   │   ├── similarity.py        # cosine (dot product) + top-N
│   │   └── recommender.py       # service tying everything together
│   ├── templates/index.html
│   └── static/{style.css, app.js}
├── scripts/train_model.py   # train + save model and product vectors
├── scripts/evaluate.py      # Precision@K check
├── tests/test_api.py
├── data/                    # put AcmeRetail_Products_70000.csv here
└── models/                  # generated model files
```

## Run in VS Code
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

python -m scripts.train_model   # one-time, ~2 min -> saves models/
uvicorn app.main:app --reload   # open http://127.0.0.1:8000
```
API docs (Swagger): http://127.0.0.1:8000/docs

If the model files are missing, the app trains automatically on first start.
Using your Colab model instead? Copy `acme_fasttext.model` (and its `.npy` files) into `models/`.

## Endpoints
| Method | URL | Purpose |
|---|---|---|
| GET | `/api/recommend/{product_id}?top_n=10&category=` | similar to a catalogue product |
| POST | `/api/recommend/text` `{"text": "...", "top_n": 10}` | similar to free text |
| GET | `/api/products/search?q=` | find product IDs by name |
| GET | `/api/categories`, `/api/health`, `/api/products/random` | helpers |

## Design notes (for your explanation video)
- **Text** = name + main_category + sub_category -> lower-case, symbols removed, stop-words removed.
- **Representation** = FastText skip-gram (100-d, char n-grams 3–6) trained on the catalogue; a product vector is the mean of its word vectors, L2-normalised.
- **Similarity** = cosine (a dot product, because vectors are normalised); top-N via partial sort.
- **Unseen words** = FastText composes vectors from character n-grams, so typos and new words still work.
- **Evaluation** = `python -m scripts.evaluate` (Precision@10 on 500 random products).
- Pre-trained models: none; FastText is trained from scratch with gensim.
=======

Last updated: October 14, 2026
>>>>>>> 4951d43d077619a2619b13d172295263ce94bcbe
