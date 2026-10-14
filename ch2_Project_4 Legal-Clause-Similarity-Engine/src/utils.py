
from pathlib import Path
import joblib
import pandas as pd
from gensim.models import Word2Vec

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


def load_word2vec():
    model_path = MODELS_DIR / "legal_word2vec.model"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Word2Vec model not found: {model_path}"
        )

    return Word2Vec.load(str(model_path))


def load_clause_data():
    """Load the saved legal clause dataset."""

    candidates = [
        MODELS_DIR / "legal_clause_data.pkl",
        MODELS_DIR / "clause.pkl",
    ]

    for path in candidates:
        if not path.exists():
            continue

        data = joblib.load(path)

        if isinstance(data, pd.DataFrame):
            if any(
                col in data.columns
                for col in ["clause_text", "text", "clause"]
            ):
                return data

        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                data = pd.DataFrame(data)
                if any(
                    col in data.columns
                    for col in ["clause_text", "text", "clause"]
                ):
                    return data

    raise ValueError(
        "No suitable clause dataset found. "
        "Check the contents of legal_clause_data.pkl and clause.pkl."
    )
