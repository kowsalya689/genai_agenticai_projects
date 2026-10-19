"""Text cleaning utilities.

Preserves the exact cleaning logic from the training notebook
(NX-NLP-2026-014). Cleaning repairs two source artefacts found in the
news-article corpus and must be applied *before* normalization so that the
inference pipeline sees text in the same shape the model was trained on:

1. Literal carriage-return / newline sequences are collapsed to a space.
2. A missing space is inserted wherever sentence-ending punctuation is glued
   directly onto the capital letter that starts the next sentence.
3. A leading wire-service dateline prefix (e.g. ``"KARACHI: "``) is stripped.
4. Repeated whitespace is collapsed.

Note: cleaning deliberately does *not* lowercase or strip general punctuation;
that is the responsibility of :mod:`app.utils.text_normalizer`.
"""

import re

# Compiled once at import for efficiency. Patterns are identical to the notebook.
DATELINE_RE = re.compile(r'^[A-Z][A-Za-z .]{1,25}:\s*')
GLUED_SENTENCE_RE = re.compile(r'([.!?])([A-Z])')


def clean_text(text: str) -> str:
    """Clean a single raw article / seed string.

    Args:
        text: Raw input text.

    Returns:
        The cleaned text, with datelines removed and sentences un-glued.
    """
    text = str(text)
    text = re.sub(r'[\r\n]+', ' ', text)          # collapse literal CRLF sequences
    text = GLUED_SENTENCE_RE.sub(r'\1 \2', text)  # un-glue sentence boundaries
    text = DATELINE_RE.sub('', text.strip())      # strip leading wire-service dateline
    text = re.sub(r'\s+', ' ', text).strip()      # collapse whitespace
    return text
