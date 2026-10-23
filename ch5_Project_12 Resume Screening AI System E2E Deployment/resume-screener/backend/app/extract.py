"""Task 10: contact details, name, designation, years of experience.

Regex for email / phone / links (transformer NER shreds them). A resume NER
model (optional) adds the designation; the name comes from the header line.
Contact details are for display only and never used in scoring (spec 4.8).
"""
import logging
import re
from datetime import date

from .config import NER_MODEL, USE_NER

log = logging.getLogger("screener.extract")

EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w/])(?:\+?\d[\d\s().\-]{8,16}\d)(?![\w])")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_]+", re.I)


def extract_contact(text: str) -> dict:
    email = EMAIL.search(text)
    phone = ""
    for m in PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            phone = m.group(0).strip()
            break
    li, gh = LINKEDIN.search(text), GITHUB.search(text)
    return {
        "email": email.group(0) if email else "",
        "phone": phone,
        "linkedin": re.sub(r"^https?://(www\.)?", "", li.group(0)) if li else "",
        "github": re.sub(r"^https?://(www\.)?", "", gh.group(0)) if gh else "",
    }


def _header_lines(text: str, n: int = 8) -> list[str]:
    return [l.strip() for l in text.split("\n") if l.strip()][:n]


def guess_name(text: str) -> str:
    for line in _header_lines(text, 5):
        if "@" in line or re.search(r"\d", line) or "|" in line:
            continue
        words = line.replace(",", " ").split()
        if 1 < len(words) <= 4 and all(re.fullmatch(r"[A-Za-z.'\-]+", w) for w in words):
            return " ".join(w.capitalize() if w.isupper() or w.islower() else w for w in words)
    return ""


def guess_designation_and_location(text: str) -> tuple[str, str]:
    lines = _header_lines(text, 6)
    desig, loc = "", ""
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if "@" in line or "|" in line or re.search(r"\d{5,}", line):
            first = line.split("|")[0].strip()
            if not loc and first and "@" not in first and not re.search(r"\d", first):
                loc = first
            break
        if not desig and 1 <= len(line.split()) <= 8:
            desig = line
    return desig, loc


# ------------------------------------------------------------- optional NER
_ner = None
_ner_failed = False


def _get_ner():
    global _ner, _ner_failed
    if USE_NER in ("0", "false", "off") or _ner_failed:
        return None
    if _ner is None:
        try:
            from transformers import pipeline
            _ner = pipeline("ner", model=NER_MODEL, aggregation_strategy="simple", device=-1)
            log.info("NER model loaded: %s", NER_MODEL)
        except Exception as e:
            log.warning("NER model unavailable (%s); using heuristics only", e)
            _ner_failed = True
            return None
    return _ner


def ner_entities(text: str) -> dict[str, list[str]]:
    ner = _get_ner()
    if ner is None:
        return {}
    head = "\n".join(_header_lines(text, 40))[:1500]
    try:
        ents = ner(head)
    except Exception as e:
        log.warning("NER failed: %s", e)
        return {}
    out: dict[str, list[str]] = {}
    for e in ents:
        if e["score"] < 0.60:
            continue
        v = e["word"].replace(" ##", "").strip()
        if len(v) < 2:
            continue
        out.setdefault(e["entity_group"], [])
        if v not in out[e["entity_group"]]:
            out[e["entity_group"]].append(v)
    return out


# ----------------------------------------------------------------- years
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

STATED = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:[A-Za-z/&\-]+\s+){0,4}?experience", re.I)
RANGE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})\s*[-–—]\s*"
    r"(present|current|now|till date|(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?\d{4})",
    re.I)


def _month_index(y: int, m: int) -> int:
    return y * 12 + (m - 1)


def computed_years(text: str, today: date | None = None) -> float | None:
    """Union of 'Mon YYYY - Mon YYYY|Present' ranges, so overlapping roles
    are not double counted. Education ranges (year-only) are ignored."""
    today = today or date.today()
    spans = []
    for m in RANGE.finditer(text):
        s = _month_index(int(m.group(2)), MONTHS[m.group(1).lower()[:3]])
        end = m.group(3).lower()
        if end[0].isalpha() and end.split()[0] in ("present", "current", "now", "till"):
            e = _month_index(today.year, today.month)
        else:
            parts = end.replace(".", " ").split()
            year = int(parts[-1])
            mon = MONTHS[parts[0][:3]] if len(parts) > 1 else 12
            e = _month_index(year, mon)
        if e >= s:
            spans.append((s, e + 1))
    if not spans:
        return None
    spans.sort()
    total, cur_s, cur_e = 0, *spans[0]
    for s, e in spans[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            total += cur_e - cur_s
            cur_s, cur_e = s, e
    total += cur_e - cur_s
    return round(total / 12, 1)


def candidate_years(text: str) -> tuple[float | None, str]:
    stated = STATED.search(text)
    if stated:
        return float(stated.group(1)), "stated"
    comp = computed_years(text)
    if comp is not None:
        return comp, "from dates"
    return None, "unknown"


def jd_years(text: str) -> tuple[float | None, float | None]:
    """(min, max) years required, parsed from the raw JD."""
    rng = re.search(r"(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*\+?\s*(?:years?|yrs?)", text, re.I)
    if rng:
        return float(rng.group(1)), float(rng.group(2))
    plus = re.findall(r"(\d+)\s*\+?\s*(?:years?|yrs?)", text, re.I)
    if plus:
        return float(plus[0]), None
    return None, None
