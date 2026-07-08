from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_status():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "outlook-signals-api"
    assert "time" in body


def test_health_in_openapi_schema():
    schema = client.get("/openapi.json").json()
    assert "/api/health" in schema["paths"]
