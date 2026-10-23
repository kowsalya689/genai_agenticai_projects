import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = ROOT / "sample_data"
FRONTEND_DIST = ROOT / "frontend" / "dist"

DEFAULT_MODEL = os.getenv("EMBED_MODEL", "bge-large")
NER_MODEL = os.getenv("NER_MODEL", "yashpwr/resume-ner-bert")
USE_NER = os.getenv("USE_NER", "auto").lower()  # auto | 1 | 0

MAX_FILES = 200
MAX_FILE_MB = 10
CHUNK_WORDS = 45
TOP_EVIDENCE = 3

# Weights of each score component. Components missing for a given JD
# (e.g. no "preferred skills" section) are dropped and the rest renormalised.
WEIGHTS = {
    "required": 0.30,        # semantic: JD required skills  vs resume skills/experience/projects
    "responsibilities": 0.15,  # semantic: JD duties          vs resume experience/projects
    "preferred": 0.05,       # semantic: JD nice-to-have     vs resume skills/projects/experience
    "role": 0.05,            # semantic: JD role summary     vs resume summary/experience
    "skills_must": 0.25,     # deterministic must-have skill coverage (alias aware)
    "skills_nice": 0.05,     # deterministic nice-to-have skill coverage
    "years": 0.15,           # numeric years-of-experience check
}
