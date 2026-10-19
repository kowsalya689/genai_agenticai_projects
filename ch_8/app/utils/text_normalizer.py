"""Text normalization utilities.

Preserves the exact normalization and sentence-splitting logic from the
training notebook (NX-NLP-2026-014). Normalization reduces surface-level
variation so the tokenizer sees tokens in the same form used during training:

* lowercases all text (case is not informative for this task),
* isolates the punctuation marks ``. , ? !`` as standalone, space-padded
  tokens (predicting sentence-ending punctuation is part of the task),
* strips all other non-alphanumeric symbols, and
* collapses whitespace.
"""

import re
from typing import List

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def split_sentences(text: str) -> List[str]:
    """Split cleaned text into sentences on ``.``, ``!`` and ``?``."""
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def normalize_text(text: str) -> str:
    """Normalize a single string for tokenization.

    Args:
        text: Cleaned text (typically the output of ``clean_text``).

    Returns:
        The normalized, lowercased text with punctuation isolated as tokens.
    """
    text = text.lower()
    text = re.sub(r"([.,?!])", r" \1 ", text)        # isolate kept punctuation as tokens
    text = re.sub(r"[^a-z0-9'.,?!\s]", " ", text)     # strip everything else
    text = re.sub(r"\s+", " ", text).strip()
    return text
