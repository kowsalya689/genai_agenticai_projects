"""Heuristic hallucination check: flags numbers, dates and capitalised terms in the summary that are not in the source."""
import re

from backend.services.text_utils import split_sentences

_MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_MON = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_DATE_MDY = re.compile(rf"\b({_MON})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b")
_DATE_DMY = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?({_MON})\.?,?\s+(\d{{4}})\b")
_DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'&\-]*")


def extract_dates(text: str) -> set[tuple[int, int, int]]:
    found = set()
    for m, d, y in _DATE_MDY.findall(text):
        found.add((int(y), _MONTHS[m[:3].lower()], int(d)))
    for d, m, y in _DATE_DMY.findall(text):
        found.add((int(y), _MONTHS[m[:3].lower()], int(d)))
    for y, m, d in _DATE_ISO.findall(text):
        found.add((int(y), int(m), int(d)))
    return found


def extract_numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in _NUM_RE.findall(text)}


def _norm_word(w: str) -> str:
    w = re.sub(r"'s$", "", w.lower())
    return w.rstrip("s")


def proper_terms(text: str) -> set[str]:
    out = set()
    for sent in split_sentences(text):
        for i, w in enumerate(_WORD_RE.findall(sent)):
            if len(w) >= 2 and (w.isupper() or (w[0].isupper() and i > 0)):
                out.add(w)
    return out


def faithfulness_report(source: str, summary: str) -> dict:
    src_nums, sum_nums = extract_numbers(source), extract_numbers(summary)
    bad_nums = sorted(sum_nums - src_nums)
    bad_dates = sorted(extract_dates(summary) - extract_dates(source))
    src_words = {_norm_word(w) for w in _WORD_RE.findall(source)}
    sum_terms = proper_terms(summary)
    bad_terms = sorted(w for w in sum_terms if _norm_word(w) not in src_words)
    return {
        "unsupported_numbers": bad_nums,
        "unsupported_dates": ["%04d-%02d-%02d" % d for d in bad_dates],
        "unsupported_terms": bad_terms,
        "n_numbers": len(sum_nums),
        "n_terms": len(sum_terms),
    }


def report_to_warnings(report: dict) -> list[str]:
    return (
        [f"number not found in source: {n}" for n in report["unsupported_numbers"]]
        + [f"date not found in source: {d}" for d in report["unsupported_dates"]]
        + [f"term not found in source: {t}" for t in report["unsupported_terms"]]
    )
