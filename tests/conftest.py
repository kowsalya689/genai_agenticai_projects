"""Shared test fixtures.

These fakes let the prediction service and API be tested deterministically
without TensorFlow installed and without the real trained artifacts, by
mimicking just the interface the code depends on:

* a tokenizer with ``texts_to_sequences`` / ``word_index`` / ``index_word``
* a model with ``predict(x, verbose=0)`` returning a probability array
* a bundle exposing ``model``, ``tokenizer``, ``index_word``, ``context_length``
"""

import numpy as np
import pytest


class FakeTokenizer:
    def __init__(self):
        # id 0 is reserved for padding (as in Keras).
        self.word_index = {"<OOV>": 1, "the": 2, "stock": 3, "market": 4, "rose": 5}
        self.index_word = {v: k for k, v in self.word_index.items()}

    def texts_to_sequences(self, texts):
        return [[self.word_index.get(w, 1) for w in t.split()] for t in texts]


class FakeModel:
    """Returns a fixed probability distribution regardless of input."""

    def __init__(self, probs):
        self._probs = np.asarray(probs, dtype=np.float64)

    def predict(self, x, verbose=0):
        return self._probs.reshape(1, -1)


class FakeBundle:
    def __init__(self, probs, context_length=15):
        self.tokenizer = FakeTokenizer()
        self.model = FakeModel(probs)
        self.word_index = self.tokenizer.word_index
        self.index_word = self.tokenizer.index_word
        self.context_length = context_length


# Probabilities indexed by token id: [pad, <OOV>, the, stock, market, rose]
# argmax = id 4 ("market"); descending order: market, stock, the, rose, <OOV>, pad
DEFAULT_PROBS = [0.00, 0.02, 0.10, 0.20, 0.60, 0.08]


@pytest.fixture
def default_bundle():
    return FakeBundle(DEFAULT_PROBS)


@pytest.fixture
def oov_bundle():
    """A model that always predicts the <OOV> token (id 1)."""
    return FakeBundle([0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
