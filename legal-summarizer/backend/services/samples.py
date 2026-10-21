import json
from functools import lru_cache
from pathlib import Path

_FILE = Path(__file__).resolve().parent.parent / "data" / "samples.json"


@lru_cache
def load_samples() -> list[dict]:
    return json.loads(_FILE.read_text(encoding="utf-8"))
