import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_recommend_by_id_sorted_and_excludes_self(client):
    r = client.get("/api/recommend/0?top_n=5").json()
    scores = [x["similarity"] for x in r["results"]]
    assert len(scores) == 5 and scores == sorted(scores, reverse=True)
    assert all(x["product_id"] != 0 for x in r["results"])


def test_text_query_with_unseen_word(client):
    r = client.post("/api/recommend/text", json={"text": "blorptastic running shoes", "top_n": 5})
    assert r.status_code == 200 and len(r.json()["results"]) == 5


def test_bad_inputs(client):
    assert client.get("/api/recommend/99999999").status_code == 404
    assert client.post("/api/recommend/text", json={"text": "!!!"}).status_code == 422
