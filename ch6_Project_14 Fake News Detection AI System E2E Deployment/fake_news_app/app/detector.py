"""
The brain of the app.

`FakeNewsDetector` loads the saved model, tokenizer and label map once, then
predicts REAL or FAKE for any text you give it. The prediction logic is the same
as the `FakeNewsDetector` class in the Colab notebook.

We keep a single shared detector (a "singleton") via `get_detector()` so the
big model is loaded into memory only one time, not on every request.
"""
import json
import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.config import MAX_LEN, MODEL_DIR
from app.preprocessing import clean_text


class FakeNewsDetector:
    """Loads the trained model and classifies text as REAL or FAKE."""

    def __init__(self, model_dir: str = MODEL_DIR):
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(
                f"Model folder not found: '{model_dir}'.\n"
                "Unzip fake_news_model.zip inside the project folder so that "
                "'fake_news_model/' sits next to run.py, or set the MODEL_DIR "
                "environment variable to point at your model folder."
            )

        # Use a GPU if one is available, otherwise the CPU (works fine either way).
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = (
            AutoModelForSequenceClassification.from_pretrained(model_dir)
            .to(self.device)
            .eval()
        )

        # label_map maps model output 0/1 to the words "FAKE"/"REAL".
        with open(os.path.join(model_dir, "label_map.json"), encoding="utf-8") as f:
            self.label_map = json.load(f)

    def predict(self, text: str) -> dict:
        """Return the label, a confidence score, and both class probabilities."""
        cleaned = clean_text(text)
        if not cleaned:
            raise ValueError("The text is empty after cleaning. Please enter some words.")

        encoded = self.tokenizer(
            cleaned,
            truncation=True,
            padding=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            logits = self.model(**encoded).logits
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

        idx = int(probs.argmax())
        return {
            "label": self.label_map[str(idx)],
            "confidence": round(float(probs[idx]), 4),
            "probabilities": {
                self.label_map["0"]: round(float(probs[0]), 4),
                self.label_map["1"]: round(float(probs[1]), 4),
            },
        }


# --- shared single instance -------------------------------------------------
_detector: FakeNewsDetector | None = None


def get_detector() -> FakeNewsDetector:
    """Create the detector on first use, then reuse the same one."""
    global _detector
    if _detector is None:
        _detector = FakeNewsDetector()
    return _detector
