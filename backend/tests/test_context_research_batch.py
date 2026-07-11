"""TASK-060 context selection, isolation, storage, and scheduling tests."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchUsage,
)
from app.core.context_research_batch import (
    build_research_inputs,
    run_context_research_batch,
    select_context_targets,
)
from app.core.context_verification import IndependentVerifierClient
from app.db.models import (
    Base,
    ContextCandidate,
    ContextCollectionRun,
    DataCollectionLog,
    IssueSignal,
    Market,
    MarketMetric,
    MarketOutcome,
    MarketSnapshot,
)

NOW = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
CONDITION = "Published condition is confirmed"


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    return "INTEGER"


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            Market.__table__,
            MarketOutcome.__table__,
            MarketSnapshot.__table__,
            MarketMetric.__table__,
            IssueSignal.__table__,
            ContextCandidate.__table__,
            ContextCollectionRun.__table__,
            DataCollectionLog.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_market(
    db,
    *,
    heat=10,
    change_24h=0.01,
    change_7d=0.02,
    computed_at=NOW,
    with_signal=False,
):
    market_id = uuid.uuid4()
    market = Market(
        id=market_id,
        polymarket_condition_id=f"condition-{market_id}",
        title="Will the published condition be confirmed?",
        description=CONDITION,
        category="technology",
        outcome_type="binary",
        status="active",
        market_created_at=NOW - timedelta(days=30),
        end_date=NOW + timedelta(days=30),
        first_seen_at=NOW - timedelta(days=30),
        last_seen_at=computed_at,
    )
    db.add(market)
    db.add(
        MarketOutcome(
            id=uuid.uuid4(),
            market_id=market_id,
            outcome_label="Yes",
            token_id=f"token-{market_id}",
            is_tracked=True,
        )
    )
    db.add(
        MarketSnapshot(
            market_id=market_id,
            captured_at=computed_at,
            price=0.63,
            volume_24h=1000,
            volume_total=10000,
            liquidity=2000,
            best_bid=None,
            best_ask=None,
        )
    )
    metric = MarketMetric(
        market_id=market_id,
        computed_at=computed_at,
        change_24h=change_24h,
        change_7d=change_7d,
        volatility_score=None,
        attention_score=None,
        heat_score=heat,
        confidence_level="sufficient",
    )
    db.add(metric)
    db.flush()
    if with_signal:
        db.add(
            IssueSignal(
                market_id=market_id,
                signal_type="expectation_shift",
                severity="medium",
                window="24h",
                magnitude=change_24h,
                triggered_at=computed_at,
                detail=None,
            )
        )
    db.commit()
    return market, metric


def _seed_context(db, market_id, *, collected_at=NOW, state="verified", suffix="seed"):
    row = ContextCandidate(
        id=uuid.uuid4(),
        market_id=market_id,
        episode_at=NOW - timedelta(hours=1),
        event_title="Seeded public context",
        event_at=NOW - timedelta(hours=1),
        neutral_summary="Seeded context summary.",
        sources=[],
        verification_state=state,
        verification_score_internal=1,
        research_model="openai/research",
        verifier_model="anthropic/verifier",
        policy_version="v4",
        evidence_hash=f"sha256:{suffix}:{market_id}",
        collected_at=collected_at,
        expires_at=collected_at + timedelta(hours=24),
    )
    db.add(row)
    db.commit()
    return row


def _citation(citation_id, url, content):
    return NormalizedCitation(
        citation_id=citation_id,
        url=url,
        canonical_url=url,
        title="Published condition update July 11, 2026",
        domain=url.split("/")[2],
        content_excerpt=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        retrieved_at=NOW,
    )


def _research_result(inputs, *, candidate_count=1, empty=False):
    if empty:
        return ContextResearchResult(
            model="openai/research",
            queries=["bounded query"],
            citations=[],
            candidates=[],
            usage=ResearchUsage(
                input_tokens=10,
                output_tokens=5,
                web_search_requests=1,
                cost_usd=0.01,
            ),
        )
    date_text = inputs.episode_at.strftime("%B %d, %Y").replace(" 0", " ")
    condition = inputs.tracked_condition
    contents = [
        f"{condition} in public record A dated {date_text}.",
        f"Public record B states {condition} on {date_text}.",
    ]
    citations = [
        _citation("citation:a", "https://source-a.example/story", contents[0]),
        _citation("citation:b", "https://source-b.example/report", contents[1]),
    ]
    candidates = [
        ResearchCandidateDraft(
            candidate_key=f"candidate:{index}",
            title="Public update recorded",
            event_at=inputs.episode_at,
            citation_ids=["citation:a", "citation:b"],
            matched_entities=["Published condition"],
            matched_condition=condition,
            temporal_relation="same_window",
        )
        for index in range(candidate_count)
    ]
    return ContextResearchResult(
        model="openai/research",
        queries=["bounded query"],
        citations=citations,
        candidates=candidates,
        usage=ResearchUsage(
            input_tokens=100,
            output_tokens=20,
            web_search_requests=2,
            cost_usd=0.05,
        ),
    )


class FakeResearchClient:
    def __init__(self, *, candidate_count=1, empty=False, fail_market_ids=None):
        self.candidate_count = candidate_count
        self.empty = empty
        self.fail_market_ids = set(fail_market_ids or [])
        self.calls = []

    def research(self, inputs):
        self.calls.append(inputs.market_id)
        if inputs.market_id in self.fail_market_ids:
            raise TimeoutError("provider detail must not be stored")
        return _research_result(
            inputs,
            candidate_count=self.candidate_count,
            empty=self.empty,
        )


class FakeVerifierTransport:
    def __init__(self):
        self.calls = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        candidates = json.loads(kwargs["messages"][1]["content"].split("\n", 1)[1])
        outputs = [
            {
                "candidate_key": candidate["candidate_key"],
                "accepted": True,
                "condition_match": True,
                "date_match": True,
                "source_supported": True,
                "unsupported_claims": [],
                "conflicting_citation_ids": [],
                "neutral_summary_ko": (
                    f"두 공개 출처는 {candidate['event_at'][:10]}에 관련 정보를 기록했습니다."
                ),
                "reason_code": "independent_multi_source_match",
            }
            for candidate in candidates
        ]
        response = {"verifications": outputs}
        usage = {"prompt_tokens": 50, "completion_tokens": 10, "cost": 0.02}
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(response)))],
            usage=usage,
        )


def _verifier():
    transport = FakeVerifierTransport()
    verifier = IndependentVerifierClient(
        transport,
        "anthropic/verifier",
        research_model="openai/research",
    )
    return verifier, transport


def test_selection_reasons_cover_missing_stale_change_and_signal(db):
    missing_market, _ = _seed_market(db, change_24h=0.01)
    stale_market, _ = _seed_market(db, change_24h=0.01)
    _seed_context(db, stale_market.id, collected_at=NOW - timedelta(hours=25), suffix="stale")
    change_market, _ = _seed_market(db, change_24h=0.06)
    _seed_context(db, change_market.id, suffix="change")
    signal_market, _ = _seed_market(db, change_24h=0.01, with_signal=True)
    _seed_context(db, signal_market.id, suffix="signal")

    targets = select_context_targets(db, NOW, top_heat_limit=0)
    reasons = {target.market_id: target.reasons for target in targets}

    assert reasons[missing_market.id] == ("missing_verified_context",)
    assert reasons[stale_market.id] == ("stale_verified_context",)
    assert reasons[change_market.id] == ("absolute_change_threshold",)
    assert reasons[signal_market.id] == ("new_expectation_shift",)


def test_top_heat_selection_is_capped_at_ten(db):
    markets = []
    for heat in range(12):
        market, _ = _seed_market(db, heat=heat, change_24h=0.01)
        _seed_context(db, market.id, suffix=f"heat-{heat}")
        markets.append((heat, market.id))

    targets = select_context_targets(db, NOW, change_threshold=1.0, top_heat_limit=10)

    assert len(targets) == 10
    assert {target.market_id for target in targets} == {
        market_id for _, market_id in sorted(markets, reverse=True)[:10]
    }


def test_backfill_selects_all_latest_metrics(db):
    market_a, _ = _seed_market(db, computed_at=NOW - timedelta(minutes=2))
    market_b, _ = _seed_market(db, computed_at=NOW - timedelta(minutes=1))
    _seed_context(db, market_a.id, suffix="a")
    _seed_context(db, market_b.id, suffix="b")

    targets = select_context_targets(
        db,
        NOW,
        backfill=True,
        change_threshold=1.0,
        top_heat_limit=0,
    )

    assert {target.market_id for target in targets} == {market_a.id, market_b.id}
    assert all("backfill" in target.reasons for target in targets)


def test_build_research_inputs_requires_both_change_windows(db):
    market, metric = _seed_market(db, change_7d=None)
    target = select_context_targets(db, NOW, top_heat_limit=0)[0]

    assert target.market_id == market.id
    assert target.metric_id == metric.id
    assert build_research_inputs(db, target) is None


def test_batch_stores_verified_candidates_and_secret_free_usage(db):
    market, _ = _seed_market(db, heat=90)
    verifier, transport = _verifier()

    outcomes = run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(),
        verifier,
        clock=lambda: NOW,
    )

    assert outcomes[0].status == "success"
    assert outcomes[0].accepted_count == 1
    candidate = db.query(ContextCandidate).one()
    assert candidate.verification_state == "verified"
    assert candidate.market_id == market.id
    run = db.query(ContextCollectionRun).one()
    assert run.status == "success"
    assert run.query_count == 2
    assert run.result_count == 2
    assert run.accepted_count == 1
    assert run.model_usage["research_input_tokens"] == 100
    assert run.model_usage["verifier_input_tokens"] == 50
    assert run.model_usage["research_cost_usd"] == 0.05
    assert run.model_usage["verifier_cost_usd"] == 0.02
    assert set(run.error_detail or {}).isdisjoint({"api_key", "prompt", "response"})
    assert len(transport.calls) == 1


def test_no_candidate_is_normal_and_does_not_call_verifier(db):
    _seed_market(db)
    verifier, transport = _verifier()

    outcomes = run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(empty=True),
        verifier,
        clock=lambda: NOW,
    )

    assert outcomes[0].status == "no_candidate"
    assert db.query(ContextCandidate).count() == 0
    assert db.query(ContextCollectionRun).one().status == "no_candidate"
    assert transport.calls == []


def test_only_verified_candidates_are_returned_to_downstream_report_stage(db):
    _seed_market(db)
    verifier, transport = _verifier()

    class RejectedResearchClient(FakeResearchClient):
        def research(self, inputs):
            result = _research_result(inputs)
            result.candidates[0] = result.candidates[0].model_copy(
                update={"matched_entities": ["Invented Agency"]}
            )
            return result

    outcomes = run_context_research_batch(
        db,
        NOW,
        RejectedResearchClient(),
        verifier,
        clock=lambda: NOW,
    )

    assert outcomes[0].status == "no_candidate"
    assert outcomes[0].candidate_ids == []
    assert db.query(ContextCandidate).one().verification_state == "rejected"
    assert transport.calls == []


def test_public_candidate_limit_is_three_and_extra_verified_is_withheld(db):
    _seed_market(db)
    verifier, _ = _verifier()

    outcomes = run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(candidate_count=4),
        verifier,
        clock=lambda: NOW,
    )

    assert outcomes[0].accepted_count == 3
    assert db.query(ContextCandidate).filter_by(verification_state="verified").count() == 3
    withheld = db.query(ContextCandidate).filter_by(verification_state="withheld").one()
    assert withheld.neutral_summary.startswith("검증 조건")


def test_market_failure_is_isolated_and_records_secret_free_error(db):
    failed_market, _ = _seed_market(db, heat=100)
    successful_market, _ = _seed_market(db, heat=90)
    verifier, _ = _verifier()

    outcomes = run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(fail_market_ids={failed_market.id}),
        verifier,
        clock=lambda: NOW,
    )

    by_market = {outcome.market_id: outcome for outcome in outcomes}
    assert by_market[failed_market.id].status == "failed"
    assert by_market[successful_market.id].status == "success"
    runs = {run.market_id: run for run in db.query(ContextCollectionRun).all()}
    assert runs[failed_market.id].status == "failed"
    assert runs[failed_market.id].error_detail == {"type": "TimeoutError"}
    assert runs[successful_market.id].status == "success"
    assert db.query(ContextCandidate).count() == 1


def test_duplicate_evidence_is_idempotent_and_returns_existing_candidate(db):
    _seed_market(db)
    verifier, _ = _verifier()
    research = FakeResearchClient()

    first = run_context_research_batch(db, NOW, research, verifier, clock=lambda: NOW)
    second = run_context_research_batch(db, NOW, research, verifier, clock=lambda: NOW)

    assert first[0].candidate_ids == second[0].candidate_ids
    assert db.query(ContextCandidate).count() == 1
    assert db.query(ContextCollectionRun).count() == 2


def test_provider_failure_preserves_previous_verified_candidate(db):
    market, _ = _seed_market(db)
    verifier, _ = _verifier()
    run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(),
        verifier,
        clock=lambda: NOW,
    )
    original_id = db.query(ContextCandidate).one().id

    outcomes = run_context_research_batch(
        db,
        NOW,
        FakeResearchClient(fail_market_ids={market.id}),
        verifier,
        clock=lambda: NOW,
    )

    assert outcomes[0].status == "failed"
    assert db.query(ContextCandidate).one().id == original_id


def test_budget_reservation_stops_before_provider_call(db):
    market, _ = _seed_market(db)
    db.add(
        ContextCollectionRun(
            id=uuid.uuid4(),
            market_id=market.id,
            episode_at=NOW - timedelta(hours=1),
            started_at=NOW - timedelta(hours=1),
            finished_at=NOW - timedelta(hours=1),
            status="success",
            query_count=1,
            result_count=1,
            accepted_count=1,
            model_usage={"research_cost_usd": 98.5, "verifier_cost_usd": 0.5},
            error_detail=None,
        )
    )
    db.commit()
    research = FakeResearchClient()
    verifier, _ = _verifier()

    outcomes = run_context_research_batch(
        db,
        NOW,
        research,
        verifier,
        budget_usd=100,
        cost_reservation_usd=2,
        clock=lambda: NOW,
    )

    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "budget_limit"
    assert research.calls == []
    budget_run = db.query(ContextCollectionRun).filter_by(status="partial").one()
    assert budget_run.error_detail == {"type": "budget_limit"}
