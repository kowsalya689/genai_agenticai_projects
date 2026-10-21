"""Preprocessing: whitespace/quote cleanup and an abbreviation-safe sentence splitter (from the notebook, section 4)."""
import re


def clean_text(t: str) -> str:
    t = t.replace("\r", "\n")
    t = t.replace("``", '"').replace("''", '"')      # LaTeX-style quotes
    t = re.sub(r"_{2,}", " ", t)                      # underscore rules / blank lines
    t = re.sub(r"\s+", " ", t)                        # collapse all whitespace (incl. newlines, nbsp)
    return t.strip()


_ABBR = ["Sec", "Secs", "No", "Nos", "Inc", "Ltd", "Pvt", "Co", "Corp", "LLC", "LLP", "Art", "Arts", "Cl",
         "Para", "Fig", "Ch", "Pt", "Reg", "Regs", "Subsec", "Dept", "St", "Mr", "Mrs", "Ms", "Dr", "Jr", "Sr",
         "Hon", "Gen", "Gov", "Sen", "Rep", "Prof", "Rev", "Stat", "Cir", "vs", "v", "approx", "Rs", "cf", "al",
         "etc", "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec"]
_ABBR_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, _ABBR), key=len, reverse=True)) + r")\.")
_MULTI_RE = re.compile(r"\b(U\.S\.C|U\.S\.A|U\.S|U\.K|e\.g|i\.e|a\.m|p\.m)\.")
_SPLIT_RE = re.compile(r"""(?:(?<=[.!?])|(?<=[.!?]["')\]]))\s+(?=["'(\[]?[A-Z0-9])""")
_LISTNUM_RE = re.compile(r"""(^|[.!?]["')\]]?\s+)(\d{1,2})\.(?=\s)""")


def split_sentences(text: str) -> list[str]:
    t = _MULTI_RE.sub(lambda m: m.group(0)[:-1] + "<DOT>", text)
    t = _ABBR_RE.sub(lambda m: m.group(1) + "<DOT>", t)
    t = _LISTNUM_RE.sub(lambda m: m.group(1) + m.group(2) + "<DOT>", t)
    parts = _SPLIT_RE.split(t)
    return [p.replace("<DOT>", ".").strip() for p in parts if p.strip()]
