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
from app.db.models import AiReport, ContextCandidate, Market, MarketSnapshot
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
    seed_v4_report,
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


def test_get_issue_report_legacy_rows_return_not_yet_generated(
    live_client, db_session
):
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
    assert response.json() == {"status": "not_yet_generated"}


def test_get_issue_report_v1_and_v3_tie_returns_not_yet_generated(
    live_client, db_session
):
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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


def test_get_issue_report_query_failure_returns_not_yet_generated(
    live_client, db_session, monkeypatch
):
    seed_basic_market(db_session)
    seed_ai_report(db_session, prompt_version="v3")

    def fail_query(*args, **kwargs):
        raise SQLAlchemyError("simulated report query failure")

    monkeypatch.setattr(issues_routes, "load_latest_successful_v4_report", fail_query)

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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}

    # 2. whitespace-only string rejection
    content_whitespace = report_content("v3_ws")
    content_whitespace["issue_overview"] = "   "
    report.content = content_whitespace
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}

    # 2. Above max_length (issue_overview maximum length is 600)
    content_too_long = report_content("long")
    content_too_long["issue_overview"] = "A" * 601
    report.content = content_too_long
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response_legacy_only.json() == {"status": "not_yet_generated"}

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
    assert response_mixed.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


def test_v3_report_no_report_empty_state(live_client, db_session):
    seed_basic_market(db_session)
    # No reports seeded at all

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


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
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_report_serves_verified_candidate_and_exact_stored_source(
    live_client, db_session
):
    seed_basic_market(db_session)
    report, candidate = seed_v4_report(db_session)
    assert candidate is not None

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(report.id)
    assert body["status"] == "success"
    assert body["report_version"] == "v4"
    assert body["data_as_of"].startswith("2026-07-08T09:00:00")
    assert body["episode_at"].startswith("2026-07-08T09:00:00")
    assert body["evidence_refs"] == [
        "metric:1",
        f"candidate:{CONTEXT_CANDIDATE_ID}",
    ]
    assert set(body["content"]) == {
        "issue_overview",
        "observed_change",
        "context_summary",
        "relationship_boundary",
        "what_to_check",
        "data_limitations",
        "caution_note",
    }
    public_candidate = body["context_candidates"][0]
    assert public_candidate["id"] == str(candidate.id)
    assert public_candidate["title"] == candidate.event_title
    assert public_candidate["summary"] == candidate.neutral_summary
    assert public_candidate["sources"] == [
        {
            "title": "Official context notice",
            "url": "https://example.gov/notices/context",
            "domain": "example.gov",
            "published_at": None,
            "source_type": "official",
        }
    ]
    assert "citation_id" not in public_candidate["sources"][0]
    assert "content_hash" not in public_candidate["sources"][0]


def test_v4_report_without_candidate_has_null_context_and_metric_ref_only(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_v4_report(db_session, with_candidate=False)

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["content"]["context_summary"] is None
    assert body["context_candidates"] == []
    assert body["evidence_refs"] == ["metric:1"]


def test_v4_withheld_candidate_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v4_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.verification_state = "withheld"
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_candidate_without_public_source_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v4_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.sources = []
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_candidate_episode_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v4_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    candidate.episode_at = NOW - timedelta(hours=1)
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_missing_candidate_evidence_reference_is_not_exposed(
    live_client, db_session
):
    seed_basic_market(db_session)
    report, _ = seed_v4_report(db_session)
    content = dict(report.content)
    content["evidence_refs"] = ["metric:1"]
    report.content = content
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_metric_content_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    report, _ = seed_v4_report(db_session)
    envelope = dict(report.content)
    content = dict(envelope["content"])
    content["observed_change"] = (
        "데이터 기준 시각의 값이 저장된 metric과 다르게 바뀐 문장입니다. "
        "이 문장은 충분한 길이를 갖지만 공개되어서는 안 됩니다."
    )
    envelope["content"] = content
    report.content = envelope
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_source_with_unapproved_internal_field_is_not_exposed(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_v4_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    source = dict(candidate.sources[0])
    source["source_excerpt"] = "internal text must not cross the public boundary"
    candidate.sources = [source]
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_source_url_domain_mismatch_is_not_exposed(live_client, db_session):
    seed_basic_market(db_session)
    seed_v4_report(db_session)
    candidate = db_session.get(ContextCandidate, CONTEXT_CANDIDATE_ID)
    source = dict(candidate.sources[0])
    source["url"] = "https://different.example/context"
    candidate.sources = [source]
    db_session.commit()

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_v4_data_as_of_later_than_generated_at_is_not_exposed(
    live_client, db_session
):
    seed_basic_market(db_session)
    seed_v4_report(db_session, generated_at=NOW - timedelta(minutes=1))

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")

    assert response.status_code == 200
    assert response.json() == {"status": "not_yet_generated"}


def test_openapi_exposes_strict_v4_report_schema(live_client, db_session):
    schema = live_client.get("/openapi.json").json()
    report_schema = schema["components"]["schemas"]["IssueReportResponse"]
    properties = report_schema["properties"]

    assert properties["report_version"]["const"] == "v4"
    assert {"episode_at", "evidence_refs", "context_candidates"}.issubset(properties)
    content_schema = schema["components"]["schemas"]["ReportContent"]
    assert content_schema["additionalProperties"] is False
    assert set(content_schema["properties"]) == {
        "issue_overview",
        "observed_change",
        "context_summary",
        "relationship_boundary",
        "what_to_check",
        "data_limitations",
        "caution_note",
    }
