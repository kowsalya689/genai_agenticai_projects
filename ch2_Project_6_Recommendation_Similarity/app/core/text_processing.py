"""Text cleaning: lower-case -> strip symbols -> remove stop-words (mirrors the notebook)."""
import re

# NLTK English stop-word list, bundled so the app needs no nltk download at runtime.
STOP_WORDS = frozenset("""
i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself
it its itself they them their theirs themselves what which who whom this that these those am is are was were be
been being have has had having do does did doing a an the and but if or because as until while of at by for with
about against between into through during before after above below to from up down in out on off over under again
further then once here there when where why how all any both each few more most other some such no nor not only
own same so than too very s t can will just don should now
""".split())

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_SPACES = re.compile(r"\s+")


def clean_text(text) -> str:
    text = "" if text is None else str(text)
    text = _NON_ALNUM.sub(" ", text.lower())
    return _SPACES.sub(" ", text).strip()


def remove_stopwords(text: str) -> str:
    return " ".join(w for w in text.split() if w not in STOP_WORDS)


def preprocess(text) -> str:
    """Full pipeline used for BOTH catalogue products and incoming queries."""
    return remove_stopwords(clean_text(text))


def tokenize(text) -> list[str]:
    return preprocess(text).split()
