"""TASK-010: read path against a real (SQLite, in-memory) database.

Covers the live-data branch of app/api/routes/issues.py. The pre-existing
fallback-path coverage in test_issues_contract.py is left untouched and
continues to exercise the static sample dataset (no DATABASE_URL is set in
the test environment, so those tests never hit the live path).

TASK-035 additions: `load_live_issues` itself failing (distinct from the
already-covered auxiliary/history query failures), unknown-id handling on
the history route, and multi-snapshot window filtering/ordering for the
Day 3 detail-chart readiness pass.
"""
from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import issues as issues_routes
from app.db.models import MarketSnapshot
from tests.conftest import (
    MARKET_ID,
    MARKET_ID_NO_METRIC,
    NOW,
    REPORT_ID_FAILED,
    REPORT_ID_LATEST,
    REPORT_ID_OLD,
    seed_ai_report,
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
    # Core metric fields the Day 3 detail/chart/marker path reads directly.
    assert body["current_value"] == 0.63
    assert body["change_24h"] == 0.08
    assert body["change_7d"] == 0.11
    assert body["confidence_level"] == "sufficient"
    assert body["heat_score"] == 78.4
    assert len(body["signals"]) == 1
    signal = body["signals"][0]
    assert signal["signal_type"] == "expectation_shift"
    assert signal["severity"] == "medium"
    assert signal["window"] == "24h"
    assert signal["magnitude"] == 0.08
    assert "triggered_at" in signal
    assert len(body["related_events"]) == 1
    related = body["related_events"][0]
    assert related["event_title"] == "A related context event"
    assert "event_date" in related
    assert "candidate, not a cause" in related["note"]


def test_detail_auxiliary_query_failure_keeps_core_issue(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated auxiliary query failure")

    monkeypatch.setattr(issues_routes, "load_signals_for_market", fail_query)
    monkeypatch.setattr(issues_routes, "load_related_events_for_market", fail_query)

    response = live_client.get(f"/api/issues/{MARKET_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(MARKET_ID)
    assert body["signals"] == []
    assert body["related_events"] == []


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


def test_history_query_failure_returns_empty_points(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated history query failure")

    monkeypatch.setattr(issues_routes, "load_history_points", fail_query)

    response = live_client.get(f"/api/issues/{MARKET_ID}/history?window=7d")

    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert len(body["points"]) == 0


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


def test_get_issue_report_live_data_returns_latest_successful_report(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_OLD,
        generated_at=NOW - timedelta(hours=2),
        label="older",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_FAILED,
        generated_at=NOW + timedelta(hours=1),
        status="failed",
        label="failed",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        generated_at=NOW + timedelta(minutes=5),
        label="latest",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(REPORT_ID_LATEST)
    assert body["status"] == "success"
    # input_metrics_id=1 links the report to the seeded metric row, so the
    # report's data_as_of reflects the metric snapshot rather than generated_at.
    assert body["data_as_of"].startswith("2026-07-08T09:00:00")
    assert body["content"]["issue_summary"] == "latest issue summary from stored data."


def test_get_issue_report_live_data_without_success_returns_not_yet_generated(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_FAILED,
        generated_at=NOW + timedelta(hours=1),
        status="failed",
        label="failed",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_get_issue_report_query_failure_returns_not_yet_generated(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    seed_ai_report(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated report query failure")

    monkeypatch.setattr(issues_routes, "load_latest_successful_report", fail_query)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_get_issue_report_unknown_id_live_mode_is_404(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/issues/does-not-exist/report")

    assert response.status_code == 404


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


def test_get_issue_history_unknown_id_live_mode_is_404(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/issues/does-not-exist/history")

    assert response.status_code == 404


def test_load_live_issues_failure_falls_back_to_static_sample_list(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated load_live_issues failure")

    monkeypatch.setattr(issues_routes, "load_live_issues", fail_query)

    response = live_client.get("/api/issues")

    assert response.status_code == 200
    body = response.json()
    ids = {issue["id"] for issue in body["issues"]}
    # Real seeded MARKET_ID must not leak through - the static fallback set
    # is served instead once the primary live query itself fails.
    assert str(MARKET_ID) not in ids
    assert "b3f1c2a4-0000-4000-8000-000000000001" in ids


def test_load_live_issues_failure_falls_back_to_static_sample_detail(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated load_live_issues failure")

    monkeypatch.setattr(issues_routes, "load_live_issues", fail_query)

    response = live_client.get("/api/issues/b3f1c2a4-0000-4000-8000-000000000001")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "b3f1c2a4-0000-4000-8000-000000000001"
    assert body["data_as_of"] is not None


def test_load_live_issues_failure_falls_back_to_static_sample_history(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated load_live_issues failure")

    monkeypatch.setattr(issues_routes, "load_live_issues", fail_query)

    response = live_client.get(
        "/api/issues/b3f1c2a4-0000-4000-8000-000000000001/history?window=7d"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert len(body["points"]) == 0


def test_history_multiple_snapshots_filtered_and_sorted_by_window(
    live_client, db_session
):
    """Verifies actual window-boundary filtering and ascending ordering, not
    just the single-snapshot happy path the earlier live-data test covers."""
    seed_basic_market(db_session)  # gives one snapshot at NOW (id=1)

    older_snapshots = [
        MarketSnapshot(
            id=101,
            market_id=MARKET_ID,
            captured_at=NOW - timedelta(days=10),
            price=0.50,
            volume_24h=1000,
            volume_total=40000,
            liquidity=1500,
            best_bid=0.49,
            best_ask=0.51,
        ),
        MarketSnapshot(
            id=102,
            market_id=MARKET_ID,
            captured_at=NOW - timedelta(days=2),
            price=0.55,
            volume_24h=1000,
            volume_total=45000,
            liquidity=1600,
            best_bid=0.54,
            best_ask=0.56,
        ),
        MarketSnapshot(
            id=103,
            market_id=MARKET_ID,
            captured_at=NOW - timedelta(hours=12),
            price=0.60,
            volume_24h=1000,
            volume_total=48000,
            liquidity=1800,
            best_bid=0.59,
            best_ask=0.61,
        ),
    ]
    for snapshot in older_snapshots:
        db_session.add(snapshot)
    db_session.commit()

    response_24h = live_client.get(f"/api/issues/{MARKET_ID}/history?window=24h")
    response_7d = live_client.get(f"/api/issues/{MARKET_ID}/history?window=7d")
    response_30d = live_client.get(f"/api/issues/{MARKET_ID}/history?window=30d")

    assert response_24h.status_code == 200
    points_24h = response_24h.json()["points"]
    assert [p["value"] for p in points_24h] == [0.60, 0.63]

    assert response_7d.status_code == 200
    points_7d = response_7d.json()["points"]
    assert [p["value"] for p in points_7d] == [0.55, 0.60, 0.63]

    assert response_30d.status_code == 200
    points_30d = response_30d.json()["points"]
    assert [p["value"] for p in points_30d] == [0.50, 0.55, 0.60, 0.63]
    # Ascending order (earliest first) so a chart can render left-to-right
    # without a client-side sort.
    timestamps = [p["captured_at"] for p in points_30d]
    assert timestamps == sorted(timestamps)
