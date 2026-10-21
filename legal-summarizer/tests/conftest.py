import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app
from backend.services.faithfulness import faithfulness_report, report_to_warnings


class FakeSummarizer:
    """Stands in for the BART model so API tests run instantly without torch."""
    def __init__(self, loaded=True):
        self._loaded, self.device, self.load_error = loaded, "cpu", None

    @property
    def is_loaded(self):
        return self._loaded

    def info(self):
        return {"loaded": self._loaded, "source": "fake", "device": "cpu", "target_compression": 0.2, "final_cap_tokens": 350}

    def summarize(self, text, compression=None, max_summary_tokens=None, num_beams=None):
        summary = " ".join(text.split()[:12])
        rep = faithfulness_report(text, summary)
        return {"summary": summary, "source_tokens": 100, "summary_tokens": 20, "source_words": len(text.split()),
                "summary_words": len(summary.split()), "compression_ratio": 0.2, "passes": [{"level": 1, "chunks": 1, "summary_tokens": 20}],
                "warnings": report_to_warnings(rep), "faithfulness": rep, "model": "fake", "elapsed_ms": 1}


def make_client(loaded=True, **overrides):
    settings = Settings(preload_model=False, rate_limit_per_minute=overrides.pop("rate", 0), **overrides)
    return TestClient(create_app(settings, FakeSummarizer(loaded)))


@pytest.fixture
def client():
    return make_client()
