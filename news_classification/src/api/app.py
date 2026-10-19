# Lifecycle stage 9 — Model Deployment (hand-off)

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import joblib

from src.data.preprocess import clean_text
from src.routing.store import route_article

# src/api/app.py -> project root is two levels up
ROOT = Path(__file__).resolve().parents[2]

app = FastAPI()

model = joblib.load(ROOT / "models" / "news_model.pkl")
vectorizer = joblib.load(ROOT / "models" / "tfidf_vectorizer.pkl")


class Article(BaseModel):
    text: str


@app.post("/predict")
def predict(article: Article):
    X = vectorizer.transform([clean_text(article.text)])
    category = str(model.predict(X)[0])
    route_article(article.text, category)
    return {"category": category}


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/app/")


# Mount last, so it never shadows /predict or /docs
app.mount("/app", StaticFiles(directory=ROOT / "webapp", html=True), name="webapp")