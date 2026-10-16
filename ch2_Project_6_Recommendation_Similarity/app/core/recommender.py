"""High-level service: owns the catalogue, model and vector matrix."""
import logging

import numpy as np
import pandas as pd

from app.config import Settings, settings as default_settings
from .data_loader import load_catalog
from .embeddings import embed_many, embed_text, load_fasttext, train_fasttext
from .similarity import top_n_similar

log = logging.getLogger(__name__)


class Recommender:
    def __init__(self, df: pd.DataFrame, model, vectors: np.ndarray):
        self.df, self.model, self.vectors = df, model, vectors
        self._categories = df["main_category"].str.lower().to_numpy()

    # ---------- construction ----------
    @classmethod
    def build(cls, cfg: Settings = default_settings, force_retrain: bool = False) -> "Recommender":
        df = load_catalog(cfg.catalog_path)
        if cfg.model_path.exists() and not force_retrain:
            log.info("Loading saved FastText model")
            model = load_fasttext(cfg.model_path)
        else:
            model = train_fasttext(df["processed_text"], cfg)
            cfg.model_path.parent.mkdir(parents=True, exist_ok=True)
            model.save(str(cfg.model_path))

        if cfg.vectors_path.exists() and not force_retrain:
            vectors = np.load(cfg.vectors_path)
            if len(vectors) != len(df):                      # catalogue changed -> rebuild
                vectors = None
        else:
            vectors = None
        if vectors is None:
            vectors = embed_many(df["processed_text"], model)
            np.save(cfg.vectors_path, vectors)
        return cls(df, model, vectors)

    # ---------- queries ----------
    def _format(self, idx, scores) -> list[dict]:
        rows = self.df.iloc[idx]
        out = []
        for (_, r), s in zip(rows.iterrows(), scores):
            out.append({**self._product(r), "similarity": round(float(s), 4)})
        return out

    @staticmethod
    def _product(r) -> dict:
        prod = {k: r[k] for k in ("name", "main_category", "sub_category",
                                  "image", "link", "ratings", "discount_price", "actual_price")}
        return {"product_id": int(r["product_id"]), **prod}

    def _mask(self, category: str | None):
        return None if not category else self._categories == category.lower()

    def recommend_by_id(self, product_id: int, top_n: int = 10, category: str | None = None) -> dict:
        if not 0 <= product_id < len(self.df):
            raise KeyError(product_id)
        idx, sc = top_n_similar(self.vectors[product_id], self.vectors, top_n,
                                exclude_index=product_id, mask=self._mask(category))
        return {"query": self._product(self.df.iloc[product_id]), "results": self._format(idx, sc)}

    def recommend_by_text(self, text: str, top_n: int = 10, category: str | None = None) -> dict:
        vec = embed_text(text, self.model)
        if not np.any(vec):
            raise ValueError("Query has no usable words after cleaning.")
        idx, sc = top_n_similar(vec, self.vectors, top_n, mask=self._mask(category))
        return {"query": {"text": text}, "results": self._format(idx, sc)}

    # ---------- helpers for the UI ----------
    def categories(self) -> list[str]:
        return sorted(self.df["main_category"].replace("", np.nan).dropna().unique().tolist())

    def find_products(self, q: str, limit: int = 8) -> list[dict]:
        mask = self.df["name"].str.contains(q, case=False, regex=False)
        return [self._product(r) for _, r in self.df[mask].head(limit).iterrows()]

    def random_products(self, n: int = 6) -> list[dict]:
        return [self._product(r) for _, r in self.df.sample(n).iterrows()]

    def stats(self) -> dict:
        return {"products": len(self.df), "vocab_size": len(self.model.wv),
                "vector_size": self.model.vector_size, "categories": len(self.categories())}
