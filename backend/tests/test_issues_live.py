"""TASK-010: read path against a real (SQLite, in-memory) database.

Covers the live-data branch of app/api/routes/issues.py. The pre-existing
fallback-path coverage in test_issues_contract.py is left untouched and
continues to exercise the static sample dataset (no DATABASE_URL is set in
the test environment, so those tests never hit the live path).
"""
from tests.conftest import (
    MARKET_ID,
    MARKET_ID_NO_METRIC,
    seed_basic_market,
    seed_market_without_metric,
)


def test_list_issues_live_data(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/issues")

    assert response.status_code == 200
    body = response.json()
    # SQLite stores naive datetimes (no tz round-trip like Postgres TIMESTAMPTZ),
    # so only the wall-clock value is checked here.
    assert body["data_as_of"].startswith("2026-07-08T09:00:00")
    assert len(body["issues"]) == 1
    issue = body["issues"][0]
    assert issue["id"] == str(MARKET_ID)
    assert issue["current_value"] == 0.63
    assert issue["change_24h"] == 0.08
    assert issue["confidence_level"] == "sufficient"


def test_get_issue_detail_live_data(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get(f"/api/issues/{MARKET_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["outcome_label"] == "Yes"
    assert body["status"] == "active"
    assert len(body["signals"]) == 1
    assert body["signals"][0]["signal_type"] == "expectation_shift"
    assert len(body["related_events"]) == 1
    assert "candidate, not a cause" in body["related_events"][0]["note"]


def test_get_issue_unknown_id_live_mode_is_404(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/issues/does-not-exist")

    assert response.status_code == 404


def test_get_issue_history_live_data(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get(f"/api/issues/{MARKET_ID}/history?window=7d")

    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert len(body["points"]) == 1
    assert body["points"][0]["value"] == 0.63


def test_missing_metric_yields_null_fields_and_insufficient_data(live_client, db_session):
    seed_market_without_metric(db_session)

    response = live_client.get("/api/issues")

    assert response.status_code == 200
    issue = response.json()["issues"][0]
    assert issue["id"] == str(MARKET_ID_NO_METRIC)
    assert issue["change_24h"] is None
    assert issue["change_7d"] is None
    assert issue["heat_score"] is None
    assert issue["confidence_level"] == "insufficient_data"


def test_empty_database_falls_back_to_static_sample(live_client, db_session):
    # db_session has tables but zero rows - simulates TASK-008 not having run yet.
    response = live_client.get("/api/issues")

    assert response.status_code == 200
    body = response.json()
    ids = {issue["id"] for issue in body["issues"]}
    assert "b3f1c2a4-0000-4000-8000-000000000001" in ids


def test_invalid_sort_param_is_422(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/issues?sort=not-a-real-sort")

    assert response.status_code == 422
