"""Central configuration. Every path / hyper-parameter lives here (override via env vars)."""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    # ---- paths ----
    catalog_path: Path = Path(os.getenv("CATALOG_PATH", BASE_DIR / "data" / "AcmeRetail_Products_70000.csv"))
    model_path: Path = Path(os.getenv("MODEL_PATH", BASE_DIR / "models" / "acme_fasttext.model"))
    vectors_path: Path = Path(os.getenv("VECTORS_PATH", BASE_DIR / "models" / "product_vectors.npy"))

    # ---- FastText hyper-parameters (same values as the notebook) ----
    vector_size: int = 100
    window: int = 5
    min_count: int = 2
    sg: int = 1            # skip-gram
    min_n: int = 3         # char n-gram range -> handles unseen / misspelt words
    bucket: int = 200_000   # hash buckets for n-grams (gensim default 2M = ~800 MB model)
    max_n: int = 6
    negative: int = 5
    epochs: int = 10
    workers: int = 4
    seed: int = 42

    # ---- API defaults ----
    default_top_n: int = 10
    max_top_n: int = 50


settings = Settings()
