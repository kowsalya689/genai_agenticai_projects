import io

from tests.conftest import make_client

DOC = "This Agreement is effective as of 1 July 2026 between Acme Ltd and Beta Pvt Ltd for USD 5,000."


def test_health_and_model(client):
    h = client.get("/api/v1/health").json()
    assert h["status"] == "ok" and h["model_loaded"] is True
    assert client.get("/api/v1/model").json()["loaded"] is True


def test_summarize_ok_and_headers(client):
    r = client.post("/api/v1/summarize", json={"text": DOC, "compression": 0.2})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"] and "faithfulness" in body and body["passes"][0]["level"] == 1
    assert r.headers["x-request-id"] and "x-process-time-ms" in r.headers
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_request_id_is_echoed(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "my-trace-id-12345"})
    assert r.headers["x-request-id"] == "my-trace-id-12345"


def test_validation_errors_use_the_common_shape(client):
    r = client.post("/api/v1/summarize", json={"text": "short"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = client.post("/api/v1/summarize", json={"text": DOC, "compression": 5})
    assert r.status_code == 422


def test_document_too_long():
    c = make_client(max_chars=50)
    r = c.post("/api/v1/summarize", json={"text": DOC})
    assert r.status_code == 413 and r.json()["error"]["code"] == "document_too_long"


def test_model_not_ready_returns_503():
    c = make_client(loaded=False)
    assert c.get("/api/v1/health").json()["status"] == "loading"
    r = c.post("/api/v1/summarize", json={"text": DOC})
    assert r.status_code == 503 and r.json()["error"]["code"] == "model_unavailable"


def test_extract_txt_and_rejects_bad_types(client):
    ok = client.post("/api/v1/extract", files={"file": ("nda.txt", io.BytesIO(DOC.encode()), "text/plain")})
    assert ok.status_code == 200 and ok.json()["text"] == DOC
    bad = client.post("/api/v1/extract", files={"file": ("virus.exe", io.BytesIO(b"x"), "application/octet-stream")})
    assert bad.status_code == 415


def test_extract_too_large():
    c = make_client(max_upload_mb=1)
    r = c.post("/api/v1/extract", files={"file": ("big.txt", io.BytesIO(b"a" * (1024 * 1024 + 10)), "text/plain")})
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"


def test_samples(client):
    s = client.get("/api/v1/samples").json()
    assert len(s) == 4 and {"id", "title", "text", "key_facts"} <= set(s[0])


def test_rate_limit():
    c = make_client(rate=3)
    codes = [c.post("/api/v1/summarize", json={"text": DOC}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    r = c.post("/api/v1/summarize", json={"text": DOC})
    assert r.headers["retry-after"] and r.json()["error"]["code"] == "rate_limited"


def test_cors_preflight(client):
    r = client.options("/api/v1/summarize", headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "POST"})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_frontend_is_served(client):
    r = client.get("/")
    assert r.status_code in (200, 404)  # 200 once frontend/index.html exists
