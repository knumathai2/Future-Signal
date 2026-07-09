from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ISSUE_ID = "b3f1c2a4-0000-4000-8000-000000000001"
NOT_YET_GENERATED_ISSUE_ID = "a71e9d3b-0000-4000-8000-000000000002"


def test_list_issues_has_data_as_of_and_confidence_level():
    response = client.get("/api/issues")
    assert response.status_code == 200
    body = response.json()
    assert "data_as_of" in body
    assert all("confidence_level" in issue for issue in body["issues"])


def test_get_issue_detail():
    response = client.get(f"/api/issues/{ISSUE_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == ISSUE_ID


def test_get_issue_unknown_id_is_404():
    response = client.get("/api/issues/does-not-exist")
    assert response.status_code == 404


def test_get_issue_history():
    response = client.get(f"/api/issues/{ISSUE_ID}/history?window=7d")
    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert "data_as_of" in body


def test_get_issue_history_unknown_id_is_404():
    response = client.get("/api/issues/does-not-exist/history")
    assert response.status_code == 404


def test_get_issue_report_success():
    response = client.get(f"/api/issues/{ISSUE_ID}/report")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_get_issue_report_not_yet_generated():
    response = client.get(f"/api/issues/{NOT_YET_GENERATED_ISSUE_ID}/report")
    assert response.status_code == 200
    assert response.json()["status"] == "not_yet_generated"


def test_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert "categories" in response.json()


def test_public_paths_never_use_market_terminal_vocabulary():
    schema = client.get("/openapi.json").json()
    paths = list(schema["paths"].keys())
    banned = ["market", "bet", "trade", "position", "profit"]
    for path in paths:
        for term in banned:
            assert term not in path.lower(), f"{path} leaks banned term {term!r}"
