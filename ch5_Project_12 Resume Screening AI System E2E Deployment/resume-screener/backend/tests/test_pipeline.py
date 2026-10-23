"""Run: cd backend && python -m pytest -q   (uses the offline embedder, no downloads)"""
from pathlib import Path

from app.pipeline import run_screening
from app.skills import extract_skills

S = Path(__file__).resolve().parents[2] / "sample_data"
FILES = [(p.name, p.read_bytes()) for p in sorted((S / "Resumes").glob("*.docx"))]


def test_alias_matching():
    assert "javascript" in extract_skills("Wrote JS and Node.js services")
    assert "apache spark" in extract_skills("PySpark jobs")


def test_data_engineer_jd_ranks_engineers_first():
    jd = (S / "JD" / "JD1_Senior_Data_Engineer.txt").read_text()
    out = run_screening(jd, FILES, 3, "hashing")
    top = [c["name"] for c in out["candidates"][:3]]
    assert "Aditya Sharma" in top
    assert sum(c["shortlisted"] for c in out["candidates"]) == 3
    assert all(c["email"] and c["phone"] for c in out["candidates"])


def test_analyst_jd_top_two():
    jd = (S / "JD" / "JD2_Data_Analyst_BI.txt").read_text()
    out = run_screening(jd, FILES, 5, "hashing")
    assert [c["name"] for c in out["candidates"][:2]] == ["Priya Nair", "Arjun Mehta"]


def test_name_does_not_change_score():
    jd = (S / "JD" / "JD2_Data_Analyst_BI.txt").read_text()
    name, data = FILES[0]
    a = run_screening(jd, [(name, data)], 1, "hashing")["candidates"][0]["raw_score"]
    b = run_screening(jd, [("ZZZ OTHER NAME.docx", data)], 1, "hashing")["candidates"][0]["raw_score"]
    assert a == b
