"""Task 3: preprocessing shared by JD and resumes (spec 4.2).

Two levels:
  light_clean -> keeps case + line structure (used for section splitting / display / NER)
  clean_text  -> lowercased, symbols filtered (what gets embedded)
  tokens      -> tokenised, stopwords removed (used by the offline embedder / keyword logic)

Stopwords are NOT removed before transformer embeddings: sentence-transformers
use word order and function words. They are removed for token-based features.
"""
import re

BULLETS = "•‣▪◦●·∙■□◆▶►*"

STOPWORDS = set(
    """a an the and or but if of to in on at by for with from as is are was were be been being
    this that these those it its we you your our their they he she i me my will would can could
    should may might must have has had do does did not no nor so than then there here also such
    into over under about across within per via etc including include includes etc using use used
    strong ability able looking join role team work working experience years year knowledge
    candidate ideal highly good excellent""".split()
)


def light_clean(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace("\t", " ").replace(" ", " ")
    text = re.sub(r"[–—−]", "-", text)
    text = re.sub(f"^[ ]*[{re.escape(BULLETS)}][ ]+", "- ", text, flags=re.M)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    """Same recipe as the notebook (lowercase, keep tech symbols), plus % and ~."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(f"[{re.escape(BULLETS)}]", "-", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9+#./\-,()&@:%~\n ]", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokens(text: str, drop_stopwords: bool = True) -> list[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]", text.lower())
    if drop_stopwords:
        toks = [t for t in toks if t not in STOPWORDS]
    return toks
