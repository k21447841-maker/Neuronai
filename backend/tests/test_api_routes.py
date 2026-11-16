from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_protected_routes_require_bearer_token():
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/providers").status_code == 401
