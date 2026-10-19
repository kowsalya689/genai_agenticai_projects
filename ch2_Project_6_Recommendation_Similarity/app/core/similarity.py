"""Cosine similarity + top-N ranking. Vectors are pre-normalised, so cosine == dot product."""
import numpy as np


def top_n_similar(query_vec: np.ndarray, matrix: np.ndarray, top_n: int,
                  exclude_index: int | None = None, mask: np.ndarray | None = None):
    """Return (indices, scores) sorted from most to least similar."""
    scores = matrix @ query_vec
    if exclude_index is not None:
        scores[exclude_index] = -np.inf
    if mask is not None:
        scores = np.where(mask, scores, -np.inf)
    k = min(top_n, int(np.isfinite(scores).sum()))
    if k <= 0:
        return np.array([], dtype=int), np.array([], dtype=np.float32)
    idx = np.argpartition(-scores, k - 1)[:k]          # O(n) partial sort
    idx = idx[np.argsort(-scores[idx])]                 # sort only the top-k
    return idx, scores[idx]
