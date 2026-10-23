"""Tasks 2, 7-9: JD + resume pipeline, scoring, ranking, explanations."""
import logging
import time
from dataclasses import dataclass, field

import numpy as np

from . import extract as ex
from .config import TOP_EVIDENCE, WEIGHTS
from .embedder import MODELS, Embedder, embed_cached, get_embedder
from .parsing import extract_text
from .preprocess import clean_text, light_clean
from .sections import chunk_items, split_jd, split_resume
from .skills import display, extract_skills, normalize_aliases

log = logging.getLogger("screener.pipeline")

# JD section -> resume sections it may be matched against (priority order)
SECTION_MAP = {
    "required": ["skills", "experience", "projects", "certifications"],
    "responsibilities": ["experience", "projects"],
    "preferred": ["skills", "projects", "experience", "certifications"],
    "role": ["summary", "experience"],
}
SEMANTIC_KEYS = list(SECTION_MAP)
NEEDED_RESUME_SECTIONS = {s for v in SECTION_MAP.values() for s in v}


@dataclass
class Chunks:
    display: list[str]
    vecs: np.ndarray = None


@dataclass
class JD:
    title: str
    sections: dict
    chunks: dict = field(default_factory=dict)
    must: set = field(default_factory=set)
    nice: set = field(default_factory=set)
    min_years: float | None = None
    max_years: float | None = None
    fallback: bool = False


def _embed_text(chunk: str) -> str:
    return normalize_aliases(clean_text(chunk))


def build_jd(raw: str, emb: Embedder) -> JD:
    light = light_clean(raw)
    sections, fallback, _meta = split_jd(light)
    role = sections.get("role", [])
    title = role[0] if role and len(role[0].split()) <= 12 else ""
    jd = JD(title=title, sections=sections, fallback=fallback)
    jd.min_years, jd.max_years = ex.jd_years(raw)

    req_text = " ".join(sections.get("required", []))
    resp_text = " ".join(sections.get("responsibilities", []))
    pref_text = " ".join(sections.get("preferred", []))
    jd.nice = extract_skills(pref_text)
    if req_text and not fallback:
        jd.must = extract_skills(req_text) | (extract_skills(resp_text) - jd.nice)
    else:
        jd.must = extract_skills(req_text + " " + resp_text + " " + " ".join(role))
    jd.nice -= jd.must

    for key in SEMANTIC_KEYS:
        items = sections.get(key)
        if not items:
            continue
        disp = chunk_items(items)
        c = Chunks(display=disp)
        c.vecs = embed_cached(emb, [_embed_text(t) for t in disp], is_query=True)
        jd.chunks[key] = c
    return jd


def _cal(sim: float, emb: Embedder) -> float:
    return float(min(1.0, max(0.0, (sim - emb.lo) / (emb.hi - emb.lo))))


def compare_section(jd_c: Chunks, res: dict, targets: list[str], emb: Embedder):
    """Mean over JD chunks of the best-matching resume chunk. Answers 'is every
    JD requirement covered somewhere?' without punishing extra content."""
    if "full_text" in res:
        targets = ["full_text"]
    mats, texts, srcs = [], [], []
    for t in targets:
        if t in res and len(res[t].display):
            mats.append(res[t].vecs)
            texts.extend(res[t].display)
            srcs.extend([t] * len(res[t].display))
    if not mats or not jd_c.display:
        return None, []
    R = np.vstack(mats)
    sim = jd_c.vecs @ R.T
    best_idx, best_val = sim.argmax(axis=1), sim.max(axis=1)
    score = float(np.mean([_cal(v, emb) for v in best_val]))
    evidence = [
        {"jd_chunk": jd_c.display[i], "resume_chunk": texts[int(best_idx[i])],
         "resume_section": srcs[int(best_idx[i])], "sim": round(float(best_val[i]), 4)}
        for i in range(len(best_val))
    ]
    return score, evidence


def years_fit(cand: float | None, jd_min: float | None) -> float | None:
    if jd_min is None:
        return None
    if cand is None:
        return 0.5  # unknown: neutral rather than punishing
    return float(min(1.0, cand / jd_min)) if jd_min > 0 else 1.0


def _fmt(n: float) -> str:
    return f"{n:g}"


def _snip(s: str, n: int = 240) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def run_screening(jd_text: str, resumes: list[tuple[str, bytes]], top_k: int, model_key: str) -> dict:
    t0 = time.time()
    emb = get_embedder(model_key)
    jd = build_jd(jd_text, emb)

    parsed, errors = [], []
    for name, data in resumes:
        try:
            raw = extract_text(name, data)
            parsed.append((name, raw))
        except Exception as e:
            errors.append({"file_name": name, "error": str(e)})

    # ---- split + chunk every resume, then embed all chunks in one batch
    staged = []
    all_texts: list[str] = []
    for name, raw in parsed:
        light = light_clean(raw)
        secs, fb = split_resume(light)
        per = {}
        for sec, items in secs.items():
            if sec in NEEDED_RESUME_SECTIONS or sec == "full_text":
                disp = chunk_items(items)
                per[sec] = (disp, len(all_texts), len(all_texts) + len(disp))
                all_texts.extend(_embed_text(t) for t in disp)
        staged.append((name, raw, light, secs, fb, per))
    vecs = embed_cached(emb, all_texts, is_query=False) if all_texts else np.zeros((0, 1))

    rows = []
    for name, raw, light, secs, fb, per in staged:
        res = {sec: Chunks(display=disp, vecs=vecs[a:b]) for sec, (disp, a, b) in per.items()}

        # semantic components
        comps: dict[str, float | None] = {}
        evidence_all = []
        for key in SEMANTIC_KEYS:
            if key not in jd.chunks:
                continue
            s, ev = compare_section(jd.chunks[key], res, SECTION_MAP[key], emb)
            comps[key] = s
            for e in ev:
                e["jd_section"] = key
            evidence_all.extend(ev)

        # deterministic skills (header excluded -> name/contact never matter)
        body_items = [i for k, v in secs.items() if k != "header" for i in v]
        found = extract_skills(" ".join(body_items))
        matched_must = sorted(jd.must & found)
        missing_must = sorted(jd.must - found)
        matched_nice = sorted(jd.nice & found)
        comps["skills_must"] = len(matched_must) / len(jd.must) if jd.must else None
        comps["skills_nice"] = len(matched_nice) / len(jd.nice) if jd.nice else None

        years, years_src = ex.candidate_years(raw)
        comps["years"] = years_fit(years, jd.min_years)

        active = {k: w for k, w in WEIGHTS.items() if comps.get(k) is not None}
        total_w = sum(active.values()) or 1.0
        raw_score = sum(comps[k] * w for k, w in active.items()) / total_w

        desig, loc = ex.guess_designation_and_location(light)
        ents = ex.ner_entities(light)
        if ents.get("Designation") and not desig:
            desig = ents["Designation"][0]

        evidence_all.sort(key=lambda e: e["sim"], reverse=True)
        seen, top_ev = set(), []
        for e in evidence_all:
            if e["resume_chunk"] in seen:
                continue
            seen.add(e["resume_chunk"])
            top_ev.append({**e, "jd_chunk": _snip(e["jd_chunk"]), "resume_chunk": _snip(e["resume_chunk"])})
            if len(top_ev) == TOP_EVIDENCE:
                break

        rows.append({
            "file_name": name,
            "name": ex.guess_name(light) or name.rsplit(".", 1)[0].title(),
            "designation": desig,
            "location": loc,
            **ex.extract_contact(raw),
            "years": years,
            "years_source": years_src,
            "raw_score": round(raw_score, 4),
            "breakdown": {k: (round(v * 100) if v is not None else None) for k, v in comps.items()},
            "matched_must": [display(s) for s in matched_must],
            "missing_must": [display(s) for s in missing_must],
            "matched_nice": [display(s) for s in matched_nice],
            "evidence": top_ev,
            "sections_found": sorted(k for k in secs if k != "header"),
            "used_fallback": fb,
            "ner": ents,
        })

    # ---- normalise, rank, shortlist
    rows.sort(key=lambda r: (r["raw_score"], len(r["matched_must"])), reverse=True)
    raws = [r["raw_score"] for r in rows]
    lo, hi = (min(raws), max(raws)) if raws else (0, 0)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["fit_score"] = round(r["raw_score"] * 100, 1)
        r["relative_score"] = 50.0 if hi - lo < 1e-6 else round((r["raw_score"] - lo) / (hi - lo) * 100, 1)
        r["shortlisted"] = i < top_k
        r["reason"] = _reason(r, jd)

    return {
        "meta": {
            "model": emb.label,
            "model_key": emb.key,
            "requested_model": model_key,
            "fallback_note": emb.fallback_note,
            "n_resumes": len(rows),
            "top_k": top_k,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "weights": WEIGHTS,
            "jd": {
                "title": jd.title,
                "min_years": jd.min_years,
                "max_years": jd.max_years,
                "must_skills": [display(s) for s in sorted(jd.must)],
                "nice_skills": [display(s) for s in sorted(jd.nice)],
                "sections": {k: len(v) for k, v in jd.sections.items()},
                "used_fallback": jd.fallback,
            },
        },
        "candidates": rows,
        "errors": errors,
    }


def _reason(r: dict, jd: JD) -> str:
    parts = []
    mm, miss = r["matched_must"], r["missing_must"]
    total = len(mm) + len(miss)
    if total:
        s = f"Covers {len(mm)} of {total} must-have skills"
        if mm:
            s += f" ({', '.join(mm[:5])}{'…' if len(mm) > 5 else ''})"
        if miss:
            s += f"; missing {', '.join(miss[:3])}{'…' if len(miss) > 3 else ''}"
        parts.append(s + ".")
    y = r["years"]
    if jd.min_years is not None:
        if y is None:
            parts.append("Years of experience not stated.")
        elif y >= jd.min_years:
            parts.append(f"{_fmt(y)} yrs experience meets the {_fmt(jd.min_years)}+ yr requirement.")
        else:
            parts.append(f"{_fmt(y)} yrs experience is below the {_fmt(jd.min_years)} yr requirement.")
    if r["evidence"]:
        e = r["evidence"][0]
        parts.append(f"Strongest alignment is in {e['resume_section']}.")
    return " ".join(parts)
