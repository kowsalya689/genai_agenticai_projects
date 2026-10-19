"""Tokenizer persistence and vocabulary access.

The tokenizer fitted during training is persisted with :mod:`pickle`
(``pickle.dump(tokenizer, ...)``) and reloaded here at serving time so that the
exact same word->id mapping is used for inference. No retraining occurs.

TensorFlow is intentionally *not* imported at module top level. Unpickling a
Keras ``Tokenizer`` pulls in TensorFlow lazily on demand, which keeps the API
and validation layers importable (and unit-testable) without TensorFlow
installed.
"""

import pickle
from typing import Any, Dict, Tuple


def load_tokenizer(path: str) -> Any:
    """Load a pickled Keras ``Tokenizer`` from disk."""
    with open(path, "rb") as f:
        return pickle.load(f)


def save_tokenizer(tokenizer: Any, path: str) -> None:
    """Persist a Keras ``Tokenizer`` to disk with pickle."""
    with open(path, "wb") as f:
        pickle.dump(tokenizer, f)


def get_vocab(tokenizer: Any) -> Tuple[Dict[str, int], Dict[int, str]]:
    """Return ``(word_index, index_word)`` from a fitted tokenizer.

    ``index_word`` is the reverse mapping used to decode predicted token ids
    back into human-readable words.
    """
    return tokenizer.word_index, tokenizer.index_word
