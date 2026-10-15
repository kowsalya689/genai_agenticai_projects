import csv
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import joblib

from src.data.preprocess import clean_text
from src.quarantine.store import quarantine_email, QUARANTINE_FILE

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

model = joblib.load("models/spam_model.pkl")
vectorizer = joblib.load("models/count_vectorizer.pkl")


class Email(BaseModel):
    text: str


class Release(BaseModel):
    email_text: str


@app.post("/predict")
def predict(email: Email):
    X = vectorizer.transform([clean_text(email.text)])
    label = model.predict(X)[0]
    if label == "spam":
        quarantine_email(email.text, label)
    return {"label": label}


@app.get("/quarantine")
def list_quarantine():
    if not os.path.exists(QUARANTINE_FILE):
        return []
    with open(QUARANTINE_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@app.post("/quarantine/release")
def release(item: Release):
    if not os.path.exists(QUARANTINE_FILE):
        return {"released": False}
    with open(QUARANTINE_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    kept = [r for r in rows if r["email_text"] != item.email_text]
    with open(QUARANTINE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "label", "email_text"])
        w.writeheader()
        w.writerows(kept)
    return {"released": len(kept) < len(rows)}


# Keep this LAST so it doesn't block the API routes above
app.mount("/", StaticFiles(directory="src/webapp", html=True), name="webapp")