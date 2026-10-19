"""Prediction service.

Preserves the exact next-word prediction and text-generation logic from the
training notebook (NX-NLP-2026-014), including top-k prediction and temperature
sampling. Wrapped in a class so the loaded model/tokenizer are injected once and
reused across requests.

Padding is performed by :func:`_pad_pre`, a dependency-free reimplementation of
``keras.preprocessing.sequence.pad_sequences(..., padding="pre",
truncating="pre")`` for a single sequence. This is numerically identical to the
notebook's padding while keeping this service importable and unit-testable
without TensorFlow. (The Keras model itself is still a TensorFlow object,
loaded in ``model_loader``.)
"""

from typing import Any, List, Tuple

import numpy as np


def _pad_pre(token_ids: List[int], maxlen: int) -> np.ndarray:
    """Pre-pad / pre-truncate a single token sequence to ``maxlen``.

    Equivalent to Keras ``pad_sequences([token_ids], maxlen=maxlen,
    padding="pre", truncating="pre")`` — zeros are added to the front, and if
    the sequence is longer than ``maxlen`` the *last* ``maxlen`` tokens are kept.

    Returns:
        A ``(1, maxlen)`` int array ready for ``model.predict``.
    """
    seq = list(token_ids)[-maxlen:]                      # truncate "pre"
    if len(seq) < maxlen:
        seq = [0] * (maxlen - len(seq)) + seq            # pad "pre"
    return np.array([seq], dtype=np.int64)


class PredictorService:
    """Stateless-per-request wrapper around a loaded model bundle."""

    def __init__(self, bundle: Any):
        self.model = bundle.model
        self.tokenizer = bundle.tokenizer
        self.index_word = bundle.index_word
        self.context_length = bundle.context_length

    # -- internal helpers ---------------------------------------------------
    def _encode(self, text: str) -> np.ndarray:
        """Clean, normalize, tokenize, and pad a raw string for the model."""
        # Imported here to avoid a hard import cycle and keep utils swappable.
        from app.utils.text_cleaner import clean_text
        from app.utils.text_normalizer import normalize_text

        cleaned = normalize_text(clean_text(text))
        token_list = self.tokenizer.texts_to_sequences([cleaned])[0]
        return _pad_pre(token_list, self.context_length)

    # -- public API ---------------------------------------------------------
    def predict_next_word(self, seed_text: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Return the top-``k`` most probable next words with probabilities.

        Mirrors the notebook's ``predict_next_word``.
        """
        token_list = self._encode(seed_text)
        probs = self.model.predict(token_list, verbose=0)[0]

        top_k = max(1, min(top_k, len(probs)))
        top_indices = probs.argsort()[-top_k:][::-1]

        results: List[Tuple[str, float]] = []
        for idx in top_indices:
            word = self.index_word.get(int(idx), "<OOV>")
            results.append((word, float(probs[idx])))
        return results

    def generate_text(self, seed_text: str, num_words: int = 12,
                      temperature: float = 0.8) -> str:
        """Generate a multi-word continuation from a seed.

        Supports greedy decoding (``temperature <= 0``) and temperature
        sampling. Mirrors the notebook's ``generate_text``.
        """
        from app.utils.text_cleaner import clean_text
        from app.utils.text_normalizer import normalize_text

        text = normalize_text(clean_text(seed_text))
        for _ in range(num_words):
            token_list = self.tokenizer.texts_to_sequences([text])[0]
            token_list = _pad_pre(token_list, self.context_length)
            probs = self.model.predict(token_list, verbose=0)[0]

            if temperature <= 0:
                next_id = int(np.argmax(probs))                     # greedy
            else:
                logits = np.log(np.clip(probs, 1e-9, 1.0)) / temperature
                scaled = np.exp(logits) / np.sum(np.exp(logits))
                next_id = int(np.random.choice(len(scaled), p=scaled))  # sampling

            next_word = self.index_word.get(next_id, "")
            if not next_word or next_word == "<OOV>":
                break
            text += " " + next_word
        return text
