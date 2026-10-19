"""Tests for the preprocessing utilities (pure-Python, no TensorFlow)."""

from app.utils.text_cleaner import clean_text
from app.utils.text_normalizer import normalize_text, split_sentences


def test_clean_removes_wire_service_dateline():
    assert clean_text("KARACHI: The government met today.") == "The government met today."


def test_clean_unglues_sentences():
    # Sentence-ending punctuation glued to the next capital letter gets a space.
    out = clean_text("prices fell.Sources said the drop was sharp.")
    assert "fell. Sources" in out


def test_clean_collapses_newlines_and_whitespace():
    assert clean_text("hello\r\n\r\n   world") == "hello world"


def test_normalize_lowercases_and_isolates_punctuation():
    out = normalize_text("The Stock Market, Rose!")
    # Lowercased, punctuation isolated as standalone tokens.
    assert out == "the stock market , rose !"


def test_normalize_strips_unknown_symbols():
    assert normalize_text("cost was $5 (approx) @ noon") == "cost was 5 approx noon"


def test_split_sentences():
    sents = split_sentences("First sentence. Second one! Third?")
    assert sents == ["First sentence.", "Second one!", "Third?"]


def test_clean_then_normalize_pipeline():
    raw = "LONDON: Shares rose 3%.Traders were upbeat."
    out = normalize_text(clean_text(raw))
    assert out.startswith("shares rose 3")
    assert "traders were upbeat" in out
