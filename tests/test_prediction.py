"""Tests for PredictorService using fake model/tokenizer (no TensorFlow)."""

import numpy as np

from app.services.predictor import PredictorService, _pad_pre


def test_pad_pre_pads_front():
    out = _pad_pre([2, 3], maxlen=5)
    assert out.tolist() == [[0, 0, 0, 2, 3]]


def test_pad_pre_truncates_front():
    out = _pad_pre([1, 2, 3, 4, 5, 6], maxlen=3)
    assert out.tolist() == [[4, 5, 6]]


def test_predict_next_word_top_k_ordering(default_bundle):
    svc = PredictorService(default_bundle)
    preds = svc.predict_next_word("the stock", top_k=3)
    words = [w for w, _ in preds]
    probs = [p for _, p in preds]
    # market (0.60) > stock (0.20) > the (0.10)
    assert words == ["market", "stock", "the"]
    assert probs == sorted(probs, reverse=True)


def test_predict_next_word_respects_top_k(default_bundle):
    svc = PredictorService(default_bundle)
    assert len(svc.predict_next_word("the", top_k=5)) == 5


def test_generate_greedy_is_deterministic(default_bundle):
    svc = PredictorService(default_bundle)
    # Greedy always appends the argmax word ("market").
    out = svc.generate_text("the stock", num_words=3, temperature=0)
    assert out == "the stock market market market"


def test_generate_stops_on_oov(oov_bundle):
    svc = PredictorService(oov_bundle)
    # Model always predicts <OOV>, so generation stops immediately.
    out = svc.generate_text("the stock", num_words=10, temperature=0)
    assert out == "the stock"


def test_generate_temperature_sampling_is_seeded(default_bundle):
    svc = PredictorService(default_bundle)
    np.random.seed(123)
    a = svc.generate_text("the", num_words=4, temperature=0.8)
    np.random.seed(123)
    b = svc.generate_text("the", num_words=4, temperature=0.8)
    assert a == b  # same seed -> same sampled continuation
