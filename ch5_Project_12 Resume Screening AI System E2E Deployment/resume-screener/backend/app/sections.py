"""Tasks 4 & 5: split resumes and JDs into sections, then into chunks.

Works on light-cleaned text (case preserved) so wrapped bullet lines can be
re-joined reliably and evidence shown to recruiters keeps its original casing.
"""
import re

from .config import CHUNK_WORDS

SEPARATOR = re.compile(r"^[\s\-=_*#~.|]{3,}$")


def _norm(s: str) -> str:
    s = s.lower().replace("&", " and ")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- resume
RESUME_HEADINGS = {
    "summary": ["summary", "professional summary", "career summary", "profile", "professional profile",
                "about me", "about", "objective", "career objective"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technical expertise",
               "technologies", "tech stack", "skill set", "core skills", "skills and tools",
               "technical skills and tools"],
    "experience": ["experience", "work experience", "professional experience", "employment history",
                   "work history", "career history", "employment", "relevant experience"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project experience",
                 "selected projects"],
    "education": ["education", "academic background", "academic qualifications",
                  "educational qualification", "qualifications", "education and training"],
    "certifications": ["certifications", "certification", "courses", "training",
                       "licenses and certifications", "certifications and courses"],
    "achievements": ["achievements", "awards", "accomplishments", "honors", "publications",
                     "extracurricular", "achievements and awards", "awards and achievements",
                     "awards and honors"],
}
_RESUME_LOOKUP = {_norm(v): k for k, vs in RESUME_HEADINGS.items() for v in vs}


def match_resume_heading(line: str):
    if line.startswith("-") or len(line) > 45:
        return None
    n = _norm(line)
    if not n or len(n.split()) > 5:
        return None
    return _RESUME_LOOKUP.get(n)


def _group_items(lines: list[str]) -> list[str]:
    """Re-join hard-wrapped lines: a lowercase-starting line continues an open
    previous line; a '-' line starts a new bullet."""
    items: list[str] = []
    open_prev = False
    for line in lines:
        is_bullet = line.startswith("-")
        cont = items and open_prev and not is_bullet and (line[0].islower() or line[0].isdigit() or line[0] in "(&")
        text = line.lstrip("- ").strip() if is_bullet else line
        if cont:
            items[-1] += " " + text
        else:
            items.append(text)
        open_prev = not line.rstrip().endswith((".", ":", ";", "!", "?"))
    return [i for i in items if i]


def split_resume(text: str):
    """Returns ({section: [items]}, used_fallback)."""
    sections: dict[str, list[str]] = {}
    current, buf = "header", []

    def flush():
        if buf:
            sections.setdefault(current, []).extend(buf)

    for raw in text.split("\n"):
        line = raw.strip()
        if not line or SEPARATOR.match(line):
            continue
        h = match_resume_heading(line)
        if h:
            flush()
            current, buf = h, []
        else:
            buf.append(line)
    flush()

    out = {k: _group_items(v) for k, v in sections.items()}
    out = {k: v for k, v in out.items() if v}
    if len([k for k in out if k != "header"]) < 2:
        return {"full_text": _strip_personal(text)}, True
    return out, False


CONTACT_LINE = re.compile(r"@|linkedin\.com|github\.com|\+?\d[\d\s().\-]{8,}\d", re.I)


def _strip_personal(text: str) -> list[str]:
    """Fallback for unstructured resumes: drop the name and contact lines so
    personal details never take part in scoring (spec 4.8)."""
    lines = [l.strip() for l in text.split("\n") if l.strip() and not SEPARATOR.match(l.strip())]
    if lines and len(lines[0].split()) <= 4 and not re.search(r"\d", lines[0]):
        lines = lines[1:]
    lines = [l for l in lines if not CONTACT_LINE.search(l)]
    return _group_items(lines)


# -------------------------------------------------------------------- JD
JD_HEADINGS = {
    "role": ["job title", "title", "role", "position", "designation", "about the role", "role overview",
             "job summary", "about the job", "overview", "summary"],
    "required": ["required skills", "requirements", "must have", "must haves", "required qualifications",
                 "skills required", "key skills", "technical skills", "what we are looking for",
                 "who you are", "essential skills", "mandatory skills", "technical requirements",
                 "qualifications", "required skills and experience", "what you bring"],
    "preferred": ["preferred skills", "nice to have", "good to have", "bonus", "preferred qualifications",
                  "desirable", "plus points", "added advantage", "bonus points", "preferred"],
    "responsibilities": ["responsibilities", "key responsibilities", "what you will do", "what you ll do",
                         "duties", "job description", "your role", "day to day", "what youll do"],
    "experience": ["experience", "experience required", "work experience", "years of experience",
                   "eligibility"],
    "company": ["about us", "about the company", "who we are", "company overview"],
    "benefits": ["benefits", "what we offer", "perks", "compensation", "salary"],
}
_JD_LOOKUP = {_norm(v): k for k, vs in JD_HEADINGS.items() for v in vs}
JD_DROP = {"company", "benefits"}
JD_META = re.compile(r"^(location|employment type|job type|work mode)\s*:", re.I)


def _jd_heading(line: str):
    """Returns (section, inline_content) or (None, '')."""
    raw = line.strip()
    if not raw or set(raw) <= set("-=_#* "):
        return None, ""
    if raw[0] in "-•" and not raw.startswith("---"):
        return None, ""
    bare = raw.strip("#").strip().replace("*", "").replace("_", "").strip()
    head, sep, rest = bare.partition(":")
    if sep:
        sec = _JD_LOOKUP.get(_norm(head))
        if sec and len(head.split()) <= 6:
            return sec, rest.strip()
    n = _norm(bare)
    if len(n.split()) <= 6 and not bare.endswith("."):
        sec = _JD_LOOKUP.get(n)
        if sec:
            return sec, ""
    return None, ""


def split_jd(text: str):
    """Returns ({section: [items]}, used_fallback, meta_lines)."""
    sections: dict[str, list[str]] = {}
    current, buf, meta = "role", [], []

    def flush():
        if buf:
            sections.setdefault(current, []).extend(buf)

    for raw in text.split("\n"):
        line = raw.strip()
        if not line or set(line) <= set("-=_#* ") or SEPARATOR.match(line):
            continue
        line = line.replace("**", "")
        if re.match(r"^\*\s+", line):
            line = "- " + line[1:].strip()
        sec, inline = _jd_heading(line)
        if sec:
            flush()
            current, buf = sec, [inline] if inline else []
        elif JD_META.match(line.lstrip("# ")):
            meta.append(line)
        else:
            buf.append(line)
    flush()

    out = {k: _group_items(v) for k, v in sections.items() if k not in JD_DROP}
    out = {k: v for k, v in out.items() if v}
    if not any(k in out for k in ("required", "responsibilities", "preferred")):
        flat = _group_items([l.strip().replace("**", "") for l in text.split("\n")
                             if l.strip() and not SEPARATOR.match(l.strip())])
        return {"required": flat, "responsibilities": flat}, True, meta
    return out, False, meta


# ----------------------------------------------------------------- chunks
def chunk_items(items: list[str], max_words: int = CHUNK_WORDS) -> list[str]:
    """Group whole items under a word budget; never split an item so a bullet
    stays intact and can be quoted as evidence."""
    chunks, buf, count = [], [], 0
    for it in items:
        n = len(it.split())
        if count + n > max_words and buf:
            chunks.append(" · ".join(buf))
            buf, count = [], 0
        buf.append(it)
        count += n
    if buf:
        chunks.append(" · ".join(buf))
    return chunks
