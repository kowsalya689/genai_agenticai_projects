"""FastText training / loading and text -> vector conversion."""
import logging
from pathlib import Path

import numpy as np
from gensim.models import FastText

from app.config import Settings
from .text_processing import tokenize

log = logging.getLogger(__name__)


def train_fasttext(processed_texts, cfg: Settings) -> FastText:
    sentences = [t.split() for t in processed_texts if t]
    log.info("Training FastText on %d documents ...", len(sentences))
    return FastText(
        sentences=sentences,
        vector_size=cfg.vector_size, window=cfg.window, min_count=cfg.min_count,
        workers=cfg.workers, sg=cfg.sg, min_n=cfg.min_n, max_n=cfg.max_n,
        negative=cfg.negative, epochs=cfg.epochs, seed=cfg.seed, bucket=cfg.bucket,
    )


def load_fasttext(path: Path) -> FastText:
    return FastText.load(str(path))


def embed_text(text, model: FastText) -> np.ndarray:
    """Mean of word vectors, L2-normalised. FastText builds vectors for unseen words
    from character n-grams, so out-of-vocabulary words never break the system."""
    tokens = tokenize(text)
    if not tokens:
        return np.zeros(model.vector_size, dtype=np.float32)
    vec = np.mean([model.wv[t] for t in tokens], axis=0)
    norm = np.linalg.norm(vec)
    return (vec / norm).astype(np.float32) if norm > 0 else vec.astype(np.float32)


def embed_many(texts, model: FastText) -> np.ndarray:
    return np.vstack([embed_text(t, model) for t in texts]).astype(np.float32)
