import pytest
from fastapi.testclient import TestClient

from app.api.routes import categories as categories_routes
from app.api.routes import issues as issues_routes
from app.main import app

client = TestClient(app)

ISSUE_ID = "b3f1c2a4-0000-4000-8000-000000000001"
NOT_YET_GENERATED_ISSUE_ID = "a71e9d3b-0000-4000-8000-000000000002"


@pytest.fixture(autouse=True)
def force_static_fallback():
    """Keep fallback contract tests independent of configured development DBs."""

    def override():
        yield None

    app.dependency_overrides[categories_routes._get_optional_db] = override
    app.dependency_overrides[issues_routes._get_optional_db] = override
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def test_list_issues_has_data_as_of_and_confidence_level():
    response = client.get("/api/issues")
    assert response.status_code == 200
    body = response.json()
    assert "data_as_of" in body
    assert all("confidence_level" in issue for issue in body["issues"])


def test_list_issues_category_filter_is_case_insensitive_in_fallback():
    response = client.get("/api/issues?category=Environment")
    assert response.status_code == 200
    body = response.json()
    assert len(body["issues"]) == 1
    assert body["issues"][0]["category"] == "environment"


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


def test_static_fallback_report_is_not_fabricated():
    response = client.get(f"/api/issues/{ISSUE_ID}/report")
    assert response.status_code == 200
    assert response.json()["status"] == "not_yet_generated"


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
