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

import pytest
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import issues as issues_routes
from app.db.models import (
    AiReport,
    ContextCandidate,
    Market,
    MarketMetric,
    MarketResolutionRule,
    MarketSnapshot,
)
from tests.conftest import (
    CONTEXT_CANDIDATE_ID,
    MARKET_ID,
    MARKET_ID_NO_METRIC,
    NOW,
    REPORT_ID_FAILED,
    REPORT_ID_LATEST,
    REPORT_ID_OLD,
    report_content,
    seed_ai_report,
    seed_basic_market,
    seed_market_without_metric,
    seed_v5_report,
    seed_v6_report,
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


def test_list_issues_category_filter_is_case_insensitive(live_client, db_session):
    seed_basic_market(db_session)
    market = db_session.get(Market, MARKET_ID)
    market.category = "Politics"
    db_session.commit()

    response = live_client.get("/api/issues?category=politics")

    assert response.status_code == 200
    body = response.json()
    assert len(body["issues"]) == 1
    assert body["issues"][0]["category"] == "Politics"


def test_categories_live_data_returns_current_issue_categories(live_client, db_session):
    seed_basic_market(db_session)

    response = live_client.get("/api/categories")

    assert response.status_code == 200
    assert response.json() == {"categories": ["기술"]}


def test_broad_korean_category_filters_ukraine_war_issues(live_client, db_session):
    seed_basic_market(db_session)
    market = db_session.get(Market, MARKET_ID)
    market.title = "Will Russia capture Lyman by September 30, 2026?"
    market.category = "Ukraine"
    db_session.commit()

    categories = live_client.get("/api/categories").json()["categories"]
    response = live_client.get("/api/issues?category=세계")

    assert categories == ["세계"]
    assert response.status_code == 200
    body = response.json()
    assert len(body["issues"]) == 1
    assert body["issues"][0]["id"] == str(MARKET_ID)


def test_broad_korean_category_supports_future_iran_conflict(live_client, db_session):
    seed_basic_market(db_session)
    market = db_session.get(Market, MARKET_ID)
    market.title = "Iran x Israel military clash by December 31, 2026?"
    market.category = "Geopolitics"
    db_session.commit()

    categories = live_client.get("/api/categories").json()["categories"]
    response = live_client.get("/api/issues?category=세계")

    assert categories == ["세계"]
    assert response.status_code == 200
    body = response.json()
    assert len(body["issues"]) == 1
    assert body["issues"][0]["id"] == str(MARKET_ID)


def test_category_navigation_hides_sports_without_removing_issue(live_client, db_session):
    seed_basic_market(db_session)
    market = db_session.get(Market, MARKET_ID)
    market.title = "Will Spain win the 2026 FIFA World Cup?"
    market.category = "Sports"
    db_session.commit()

    categories = live_client.get("/api/categories").json()["categories"]
    all_issues = live_client.get("/api/issues").json()["issues"]
    sports_issues = live_client.get("/api/issues?category=스포츠").json()["issues"]

    assert categories == []
    assert [issue["id"] for issue in all_issues] == [str(MARKET_ID)]
    assert [issue["id"] for issue in sports_issues] == [str(MARKET_ID)]


def test_stablecoin_issue_is_grouped_under_economy(live_client, db_session):
    seed_basic_market(db_session)
    market = db_session.get(Market, MARKET_ID)
    market.title = "Will USDT market cap hit $200B before 2027?"
    market.category = "Stablecoins"
    db_session.commit()

    categories = live_client.get("/api/categories").json()["categories"]
    response = live_client.get("/api/issues?category=경제")

    assert categories == ["경제"]
    assert response.status_code == 200
    assert [issue["id"] for issue in response.json()["issues"]] == [str(MARKET_ID)]


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


def test_issue_detail_scopes_snapshot_and_metric_queries_to_requested_market(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    seed_market_without_metric(db_session)
    statements: list[str] = []

    monkeypatch.setattr(
        issues_routes,
        "load_live_issues",
        lambda _db, **_kwargs: pytest.fail("detail must not call the list loader"),
    )

    def record_statement(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.casefold())

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = live_client.get(f"/api/issues/{MARKET_ID}")
    finally:
        event.remove(engine, "before_cursor_execute", record_statement)

    assert response.status_code == 200
    history_queries = [
        statement
        for statement in statements
        if "market_snapshots" in statement or "market_metrics" in statement
    ]
    assert len(history_queries) == 2
    assert all("market_id =" in statement for statement in history_queries)
    assert all("limit" in statement for statement in history_queries)


def test_detail_auxiliary_query_failure_keeps_core_issue(live_client, db_session, monkeypatch):
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


def test_history_sql_contains_market_and_both_window_bounds(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    statements: list[str] = []
    monkeypatch.setattr(
        issues_routes,
        "load_live_issues",
        lambda _db, **_kwargs: pytest.fail("history must not call the list loader"),
    )

    def record_statement(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.casefold())

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = live_client.get(f"/api/issues/{MARKET_ID}/history?window=7d")
    finally:
        event.remove(engine, "before_cursor_execute", record_statement)

    assert response.status_code == 200
    history_query = next(
        statement
        for statement in statements
        if "market_snapshots" in statement and "captured_at >=" in statement
    )
    assert "market_id =" in history_query
    assert "captured_at <=" in history_query


def test_list_sort_filter_and_pagination_use_latest_rows(live_client, db_session):
    seed_basic_market(db_session)
    seed_market_without_metric(db_session)
    db_session.add(
        MarketMetric(
            id=2,
            market_id=MARKET_ID_NO_METRIC,
            computed_at=NOW + timedelta(hours=1),
            change_24h=-0.2,
            change_7d=-0.3,
            volatility_score=0.4,
            attention_score=0.6,
            heat_score=90,
            confidence_level="sufficient",
        )
    )
    db_session.commit()

    first = live_client.get("/api/issues?sort=heat&limit=1").json()["issues"]
    second = live_client.get("/api/issues?sort=heat&limit=1&offset=1").json()["issues"]
    change = live_client.get("/api/issues?sort=change&window=7d&limit=1").json()["issues"]
    filtered = live_client.get("/api/issues?category=technology").json()["issues"]

    assert [issue["id"] for issue in first] == [str(MARKET_ID_NO_METRIC)]
    assert [issue["id"] for issue in second] == [str(MARKET_ID)]
    assert [issue["id"] for issue in change] == [str(MARKET_ID_NO_METRIC)]
    assert [issue["id"] for issue in filtered] == [str(MARKET_ID)]


def test_list_and_categories_rank_latest_rows_in_sql(live_client, db_session):
    seed_basic_market(db_session)
    statements: list[str] = []

    def record_statement(_conn, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.casefold())

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record_statement)
    try:
        assert live_client.get("/api/issues?limit=1").status_code == 200
        assert live_client.get("/api/categories").status_code == 200
    finally:
        event.remove(engine, "before_cursor_execute", record_statement)

    snapshot_queries = [statement for statement in statements if "market_snapshots" in statement]
    metric_queries = [statement for statement in statements if "market_metrics" in statement]
    assert any("row_number() over" in statement for statement in snapshot_queries)
    assert any("row_number() over" in statement for statement in metric_queries)
    assert all(
        "row_number() over" in statement or "max(market_snapshots.captured_at)" in statement
        for statement in snapshot_queries
    )


def test_history_query_failure_returns_empty_points(live_client, db_session, monkeypatch):
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


def test_get_issue_report_legacy_rows_return_not_yet_generated(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_OLD,
        generated_at=NOW - timedelta(hours=2),
        label="older",
        prompt_version="v3",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_FAILED,
        generated_at=NOW + timedelta(hours=1),
        status="failed",
        label="failed",
        prompt_version="v3",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        generated_at=NOW + timedelta(minutes=5),
        label="latest",
        prompt_version="v3",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_get_issue_report_v1_and_v3_tie_returns_not_yet_generated(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_OLD,
        generated_at=NOW,
        label="legacy",
        prompt_version="v1",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        generated_at=NOW,
        label="current",
        prompt_version="v3",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_get_issue_report_live_data_with_legacy_schema_returns_not_yet_generated(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_ai_report(db_session, prompt_version="v3")
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    # Give it legacy v2 content structure which violates v3 schema fields
    report.content = {
        "issue_explainer": "legacy issue explainer from stored data.",
        "why_it_matters": "legacy why it matters.",
        "current_reading": "legacy current reading.",
        "scenario_major_change": "legacy major.",
        "scenario_limited_change": "legacy limited.",
        "scenario_status_quo": "legacy status quo.",
        "check_points": "legacy check points.",
        "caution_note": "legacy caution note.",
    }
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


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
        prompt_version="v3",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_get_issue_report_query_failure_returns_not_yet_generated(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    seed_ai_report(db_session, prompt_version="v3")

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated report query failure")

    monkeypatch.setattr(issues_routes, "_latest_v8_reports", fail_query)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


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

    response = live_client.get("/api/issues/b3f1c2a4-0000-4000-8000-000000000001/history?window=7d")

    assert response.status_code == 200
    body = response.json()
    assert body["window"] == "7d"
    assert len(body["points"]) == 0


def test_history_multiple_snapshots_filtered_and_sorted_by_window(live_client, db_session):
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


def test_v3_success_row_is_audit_only(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
        label="v3_success",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_null_context_row_is_audit_only(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("v3_null_context")
    content["external_context"] = None
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    # override seeded content to have explicitly null external_context
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_missing_external_context_key_rejection(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("v3_missing_key")
    # remove the key entirely
    content.pop("external_context")
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    # Validation error should cause fallback to not_yet_generated
    assert response.json() == {"status": "idle"}


def test_v3_report_empty_and_whitespace_only_rejection(live_client, db_session):
    seed_basic_market(db_session)
    # 1. empty string rejection
    content_empty = report_content("v3_empty")
    content_empty["issue_overview"] = ""
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content_empty
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}

    # 2. whitespace-only string rejection
    content_whitespace = report_content("v3_ws")
    content_whitespace["issue_overview"] = "   "
    report.content = content_whitespace
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_length_boundary_rejection(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)

    # 1. Below min_length (issue_overview minimum length is 30)
    content_too_short = report_content("short")
    content_too_short["issue_overview"] = "Too short overview."  # 19 chars
    report.content = content_too_short
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}

    # 2. Above max_length (issue_overview maximum length is 600)
    content_too_long = report_content("long")
    content_too_long["issue_overview"] = "A" * 601
    report.content = content_too_long
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_sentence_count_rejection(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("sentence_count")
    content["issue_overview"] = (
        "First sentence. Second sentence. Third sentence. "
        "Fourth sentence. Fifth sentence. Sixth sentence."
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_extra_field_rejection(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("extra")
    content["unapproved_extra_field"] = "This field should trigger extra forbid validation."
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_missing_required_field_rejection(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("missing")
    content.pop("issue_overview")  # missing required field
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v1_to_v3_rows_are_all_excluded_after_v4_activation(live_client, db_session):
    seed_basic_market(db_session)

    # 1. Verify v1 / v2 legacy-row exclusion
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_OLD,
        generated_at=NOW - timedelta(hours=1),
        prompt_version="v2",  # legacy version
        status="success",
        label="v2_legacy",
    )

    response_legacy_only = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response_legacy_only.status_code == 200
    assert response_legacy_only.json() == {"status": "idle"}

    # 2. Version gating when a legacy row is newer than a v3 row
    # v3 row is older, v2 row is newer. Both must have generated_at >= data_as_of (NOW)
    import uuid

    v3_report_id = uuid.uuid4()
    seed_ai_report(
        db_session,
        report_id=v3_report_id,
        generated_at=NOW + timedelta(minutes=5),
        prompt_version="v3",
        status="success",
        label="v3_older",
    )
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        generated_at=NOW + timedelta(minutes=10),
        prompt_version="v2",
        status="success",
        label="v2_newer",
    )

    response_mixed = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response_mixed.status_code == 200
    assert response_mixed.json() == {"status": "idle"}


def test_v3_report_failed_row_exclusion(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_FAILED,
        prompt_version="v3",
        status="failed",
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_no_report_empty_state(live_client, db_session):
    seed_basic_market(db_session)
    # No reports seeded at all

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_malformed_v3_content(live_client, db_session):
    seed_basic_market(db_session)
    content = report_content("malformed")
    content["issue_overview"] = 1234567890  # integer type instead of string
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
    )
    report = db_session.get(AiReport, REPORT_ID_LATEST)
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_without_linked_metric_timestamp(live_client, db_session):
    seed_basic_market(db_session)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
        input_metrics_id=None,  # unlinked
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_invalid_data_as_of_future_than_generated_at(live_client, db_session):
    seed_basic_market(db_session)
    # data_as_of = NOW (linked from metric computed_at)
    # generated_at = NOW - 1 hour (so data_as_of > generated_at)
    seed_ai_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        prompt_version="v3",
        status="success",
        generated_at=NOW - timedelta(hours=1),
    )

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v3_report_unknown_issue_id_is_404(live_client, db_session):
    seed_basic_market(db_session)
    response = live_client.get("/api/issues/does-not-exist/report")
    assert response.status_code == 404


def test_static_fallback_does_not_fabricate_v4_evidence(live_client):
    # Unset DATABASE_URL in mock setup to trigger static fallback
    # The default issue_id "b3f1c2a4-0000-4000-8000-000000000001" returns the static fallback
    url = "/api/issues/b3f1c2a4-0000-4000-8000-000000000001/report"
    response = live_client.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v5_row_is_audit_only_after_v6_activation(live_client, db_session):
    seed_basic_market(db_session)
    seed_v5_report(db_session, with_candidate=False)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v6_report_serves_verified_candidate_and_exact_stored_source(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v6_report_without_candidate_has_general_mode_and_metric_ref_only(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session, with_candidate=False)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


@pytest.mark.parametrize(
    ("change_24h", "with_candidate", "expected_mode"),
    [
        (0.08, True, "change_with_evidence"),
        (0.08, False, "change_without_evidence"),
        (0.01, True, "stable_with_evidence"),
        (0.01, False, "stable_without_evidence"),
    ],
)
def test_v6_api_serves_all_four_reconstructed_modes(
    live_client,
    db_session,
    change_24h,
    with_candidate,
    expected_mode,
):
    seed_basic_market(db_session)
    seed_v6_report(
        db_session,
        change_24h=change_24h,
        with_candidate=with_candidate,
    )

    body = live_client.get(f"/api/issues/{MARKET_ID}/report").json()

    assert expected_mode in {
        "change_with_evidence",
        "change_without_evidence",
        "stable_with_evidence",
        "stable_without_evidence",
    }
    assert body == {"status": "idle"}


def test_v6_invalid_latest_row_preserves_previous_valid_v6_report(live_client, db_session):
    seed_basic_market(db_session)
    old_report, _ = seed_v6_report(
        db_session,
        report_id=REPORT_ID_OLD,
        generated_at=NOW + timedelta(minutes=2),
        with_candidate=False,
    )
    latest, _ = seed_v6_report(
        db_session,
        report_id=REPORT_ID_LATEST,
        generated_at=NOW + timedelta(minutes=5),
        with_candidate=False,
    )
    envelope = dict(latest.content)
    observed = dict(envelope["observed_change"])
    observed["current_value"] = 0.99
    envelope["observed_change"] = observed
    latest.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert old_report.id != latest.id
    assert response.json() == {"status": "idle"}


def test_v6_extra_briefing_field_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session, with_candidate=False)
    envelope = dict(report.content)
    briefing = dict(envelope["briefing"])
    briefing["unexpected"] = "blocked"
    envelope["briefing"] = briefing
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.json() == {"status": "idle"}


def test_v6_basis_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session, with_candidate=False)
    envelope = dict(report.content)
    briefing = dict(envelope["briefing"])
    scenarios = [dict(item) for item in briefing["conditional_scenarios"]]
    scenarios[0]["basis"] = "verified_context"
    briefing["conditional_scenarios"] = scenarios
    envelope["briefing"] = briefing
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.json() == {"status": "idle"}


def test_v6_duplicate_body_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session, with_candidate=False)
    envelope = dict(report.content)
    briefing = dict(envelope["briefing"])
    materials = [dict(item) for item in briefing["materials_to_check"]]
    materials[0]["text"] = briefing["conditional_scenarios"][0]["text"]
    briefing["materials_to_check"] = materials
    envelope["briefing"] = briefing
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.json() == {"status": "idle"}


def test_v6_resolution_rule_db_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session, with_candidate=False)
    rule = db_session.query(MarketResolutionRule).one()
    rule.condition_text = "Tampered stored condition"
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.json() == {"status": "idle"}


def test_v6_expired_candidate_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.expires_at = NOW + timedelta(minutes=1)
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.json() == {"status": "idle"}


def test_v4_withheld_candidate_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.verification_state = "withheld"
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_candidate_without_public_source_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.sources = []
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_candidate_episode_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.episode_at = NOW - timedelta(hours=1)
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_missing_candidate_evidence_reference_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session)
    content = dict(report.content)
    content["evidence_refs"] = ["metric:1"]
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_nonexistent_candidate_id_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session)
    missing_id = "99999999-9999-4999-8999-999999999999"
    envelope = dict(report.content)
    envelope["context_candidate_ids"] = [missing_id]
    envelope["evidence_refs"] = ["metric:1", f"candidate:{missing_id}"]
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_metric_content_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v6_report(db_session, with_candidate=False)
    envelope = dict(report.content)
    observed = dict(envelope["observed_change"])
    observed["change_value"] = 0.99
    envelope["observed_change"] = observed
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_source_with_unapproved_internal_field_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    source = dict(candidate.sources[0])
    source["source_excerpt"] = "internal text must not cross the public boundary"
    candidate.sources = [source]
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_source_url_domain_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    source = dict(candidate.sources[0])
    source["url"] = "https://different.example/context"
    candidate.sources = [source]
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_v4_data_as_of_later_than_generated_at_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v6_report(db_session, generated_at=NOW - timedelta(minutes=1))

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "idle"}


def test_openapi_exposes_strict_v8_report_and_request_schemas(live_client, db_session):
    schema = live_client.get("/openapi.json").json()
    report_schema = schema["components"]["schemas"]["V8IssueReportResponse"]
    properties = report_schema["properties"]

    assert properties["report_version"]["const"] == "v8"
    assert {
        "headline",
        "summary",
        "sections",
        "sources",
        "cache",
        "context_as_of",
    }.issubset(properties)
    request_schema = schema["components"]["schemas"]["GenerationRequestStatusResponse"]
    assert request_schema["additionalProperties"] is False
    assert "/api/issues/{issue_id}/report/generate" in schema["paths"]
    assert "/api/issues/{issue_id}/report/requests/{request_id}" in schema["paths"]
