"""API tests using FastAPI TestClient and a fake predictor (no TensorFlow)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.prediction_routes import get_predictor
from app.services.predictor import PredictorService

from tests.conftest import FakeBundle, DEFAULT_PROBS


@pytest.fixture
def client():
    """TestClient with the predictor dependency overridden by a fake."""
    def _fake_predictor():
        return PredictorService(FakeBundle(DEFAULT_PROBS))

    app.dependency_overrides[get_predictor] = _fake_predictor
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_predict_endpoint(client):
    res = client.post("/predict", json={"text": "the stock", "top_k": 3})
    assert res.status_code == 200
    body = res.json()
    assert body["input"] == "the stock"
    assert body["predictions"][0]["word"] == "market"
    assert len(body["predictions"]) == 3


def test_generate_endpoint(client):
    res = client.post("/generate", json={"text": "the stock", "num_words": 3, "temperature": 0})
    assert res.status_code == 200
    body = res.json()
    assert body["generated_text"] == "the stock market market market"
    assert body["temperature"] == 0


def test_predict_rejects_empty_text(client):
    # min_length=1 -> 422 from Pydantic validation.
    res = client.post("/predict", json={"text": "", "top_k": 3})
    assert res.status_code == 422


def test_predict_rejects_whitespace_text(client):
    # Passes min_length but fails the explicit strip() check -> 422.
    res = client.post("/predict", json={"text": "   ", "top_k": 3})
    assert res.status_code == 422


def test_predict_rejects_out_of_range_top_k(client):
    res = client.post("/predict", json={"text": "hello", "top_k": 999})
    assert res.status_code == 422


def test_generate_rejects_bad_temperature(client):
    res = client.post("/generate", json={"text": "hello", "num_words": 5, "temperature": 9})
    assert res.status_code == 422


def test_health_endpoint_shape():
    # No override: without real artifacts this reports model_loaded=false,
    # but the endpoint must still return 200 with the right schema.
    with TestClient(app) as c:
        res = c.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"status", "model_loaded", "available_models", "context_length", "vocab_size"}


def test_models_endpoint_lists_architectures():
    with TestClient(app) as c:
        res = c.get("/models")
    assert res.status_code == 200
    body = res.json()
    names = [m["name"] for m in body["models"]]
    assert names == ["lstm", "gru", "rnn"]
    assert body["default"] == "lstm"


def test_predict_accepts_model_field(client):
    res = client.post("/predict", json={"text": "the stock", "top_k": 3, "model": "gru"})
    assert res.status_code == 200
    assert res.json()["model"] == "gru"


def test_generate_echoes_model_field(client):
    res = client.post(
        "/generate",
        json={"text": "the stock", "num_words": 3, "temperature": 0.0, "model": "rnn"},
    )
    assert res.status_code == 200
    assert res.json()["model"] == "rnn"
