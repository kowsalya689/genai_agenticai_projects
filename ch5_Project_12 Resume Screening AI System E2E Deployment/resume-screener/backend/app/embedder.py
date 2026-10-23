"""Task 6: embedding models.

Default is BGE-large (as in your notebook). If sentence-transformers or the
model weights are unavailable (e.g. offline), we fall back to a built-in
subword hashing embedder (FastText-style character n-grams) so the app still
runs. The fallback is reported in the API response and shown in the UI.
"""
import logging
import math
import re
import threading
import zlib
from typing import Optional

import numpy as np

from .preprocess import tokens

log = logging.getLogger("screener.embed")

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# lo/hi: cosine range mapped to 0..1 when scoring (BGE similarities sit in a
# narrow band, so raw cosine would make every candidate look like a 70% match).
MODELS = {
    "bge-large": dict(id="BAAI/bge-large-en-v1.5", label="BGE Large v1.5", prefix=BGE_QUERY_PREFIX,
                      lo=0.50, hi=0.80, size="1.3 GB", note="Best quality. Your notebook's model."),
    "bge-small": dict(id="BAAI/bge-small-en-v1.5", label="BGE Small v1.5", prefix=BGE_QUERY_PREFIX,
                      lo=0.50, hi=0.80, size="130 MB", note="Fast, good quality."),
    "bge-m3": dict(id="BAAI/bge-m3", label="BGE-M3 (multilingual)", prefix="",
                   lo=0.35, hi=0.75, size="2.2 GB", note="Multilingual resumes."),
    "minilm": dict(id="sentence-transformers/all-MiniLM-L6-v2", label="MiniLM L6", prefix="",
                   lo=0.10, hi=0.60, size="90 MB", note="Smallest and quickest."),
    "hashing": dict(id="builtin", label="Offline subword hashing", prefix="",
                    lo=0.05, hi=0.45, size="0", note="No download. Lexical + subword, weaker semantics."),
}

_lock = threading.RLock()
_cache: dict[str, "Embedder"] = {}
_vec_cache: dict[tuple, np.ndarray] = {}
_MAX_VEC_CACHE = 20000


class Embedder:
    key: str
    label: str
    lo: float
    hi: float
    fallback_note: Optional[str] = None

    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        raise NotImplementedError


class HashingEmbedder(Embedder):
    """Word unigrams + bigrams + character 3-5grams hashed into a fixed
    space. Character n-grams give subword robustness to unseen words and
    spelling variants (spec 4.5), like FastText."""

    dim = 4096

    def __init__(self, key="hashing"):
        self.key = key
        self.label = MODELS["hashing"]["label"]
        self.lo, self.hi = MODELS["hashing"]["lo"], MODELS["hashing"]["hi"]

    def _vec(self, text: str) -> np.ndarray:
        feats: dict[str, float] = {}

        def add(f, w):
            feats[f] = feats.get(f, 0.0) + w

        toks = tokens(text)
        for i, t in enumerate(toks):
            add("w:" + t, 1.0)
            if i + 1 < len(toks):
                add("b:" + t + "_" + toks[i + 1], 0.6)
            if len(t) >= 4:
                padded = f"<{t}>"
                for n in (3, 4, 5):
                    for j in range(len(padded) - n + 1):
                        add("c:" + padded[j:j + n], 0.25)
        v = np.zeros(self.dim, dtype="float32")
        for f, w in feats.items():
            h = zlib.crc32(f.encode())
            v[h % self.dim] += (1.0 if (h >> 31) & 1 else -1.0) * w * (1.0 + math.log(1.0 + w))
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode(self, texts, is_query=False):
        if not texts:
            return np.zeros((0, self.dim), dtype="float32")
        return np.vstack([self._vec(t) for t in texts])


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, key: str):
        from sentence_transformers import SentenceTransformer  # heavy import, lazy
        spec = MODELS[key]
        self.key, self.label = key, spec["label"]
        self.lo, self.hi = spec["lo"], spec["hi"]
        self.prefix = spec["prefix"]
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
        log.info("loading %s on %s", spec["id"], device)
        self.model = SentenceTransformer(spec["id"], device=device)

    def encode(self, texts, is_query=False):
        if not texts:
            return np.zeros((0, 1), dtype="float32")
        if is_query and self.prefix:
            texts = [self.prefix + t for t in texts]
        return self.model.encode(texts, batch_size=16, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False).astype("float32")


def st_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def get_embedder(key: str) -> Embedder:
    """Load (once) the requested model; fall back to hashing on any failure."""
    if key not in MODELS:
        key = "bge-large"
    with _lock:
        if key in _cache:
            return _cache[key]
        if key == "hashing":
            emb: Embedder = HashingEmbedder()
        else:
            try:
                emb = SentenceTransformerEmbedder(key)
            except Exception as e:  # offline, not installed, OOM...
                log.warning("could not load %s (%s); using offline fallback", key, e)
                emb = HashingEmbedder()
                emb.fallback_note = (f"Could not load {MODELS[key]['label']} "
                                     f"({type(e).__name__}). Using the offline hashing embedder instead. "
                                     "Install sentence-transformers and allow the model download for full quality.")
        _cache[key] = emb
        return emb


def embed_cached(emb: Embedder, texts: list[str], is_query: bool) -> np.ndarray:
    """Encode with an in-memory cache so re-screening the same resumes is instant."""
    if not texts:
        return np.zeros((0, 1), dtype="float32")
    keys = [(emb.key, emb.label, is_query, t) for t in texts]
    missing = [t for t, k in zip(texts, keys) if k not in _vec_cache]
    if missing:
        uniq = list(dict.fromkeys(missing))
        with _lock:
            vecs = emb.encode(uniq, is_query=is_query)
        if len(_vec_cache) + len(uniq) > _MAX_VEC_CACHE:
            _vec_cache.clear()
        for t, v in zip(uniq, vecs):
            _vec_cache[(emb.key, emb.label, is_query, t)] = v
    return np.vstack([_vec_cache[k] for k in keys])
