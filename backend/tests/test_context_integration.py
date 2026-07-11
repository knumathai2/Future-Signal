"""TASK-064 end-to-end v4 evidence pipeline review fixture."""

import hashlib
import json
from types import SimpleNamespace

from app.core.ai_report import LLMUsage
from app.core.ai_report_batch import run_v4_ai_report_batch
from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchUsage,
)
from app.core.context_research_batch import run_context_research_batch
from app.core.context_verification import IndependentVerifierClient
from app.db.models import AiReport, ContextCandidate, ContextCollectionRun
from tests.conftest import MARKET_ID, NOW, seed_basic_market


class IntegrationResearchClient:
    def research(self, inputs):
        date_text = inputs.episode_at.strftime("%B %d, %Y").replace(" 0", " ")
        excerpt = (
            f"Seeded test issue. {inputs.tracked_condition} "
            f"The public record is dated {date_text}."
        )
        citation = NormalizedCitation(
            citation_id="citation:integration",
            url="https://example.gov/context/integration",
            canonical_url="https://example.gov/context/integration",
            title=f"Seeded test issue public record {date_text}",
            domain="example.gov",
            content_excerpt=excerpt,
            content_hash=hashlib.sha256(excerpt.encode()).hexdigest(),
            retrieved_at=NOW,
        )
        candidate = ResearchCandidateDraft(
            candidate_key="candidate:integration",
            title="Seeded test issue update recorded",
            event_at=inputs.episode_at,
            citation_ids=[citation.citation_id],
            matched_entities=["Seeded test issue"],
            matched_condition=inputs.tracked_condition,
            temporal_relation="same_window",
        )
        return ContextResearchResult(
            model="openai/research",
            queries=["bounded integration query"],
            citations=[citation],
            candidates=[candidate],
            usage=ResearchUsage(
                input_tokens=20,
                output_tokens=10,
                web_search_requests=1,
                cost_usd=0.01,
            ),
        )


class IntegrationVerifierTransport:
    def __init__(self):
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        candidates = json.loads(kwargs["messages"][1]["content"].split("\n", 1)[1])
        payload = {
            "verifications": [
                {
                    "candidate_key": candidate["candidate_key"],
                    "accepted": True,
                    "condition_match": True,
                    "date_match": True,
                    "source_supported": True,
                    "unsupported_claims": [],
                    "conflicting_citation_ids": [],
                    "neutral_summary_ko": (
                        "공식 공개 자료에 추적 조건 관련 정보가 기록되었습니다."
                    ),
                    "reason_code": "official_direct_match",
                }
                for candidate in candidates
            ]
        }
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(payload, ensure_ascii=False)
                    )
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.01},
        )


class IntegrationWriterClient:
    def __init__(self):
        self.usage_records = []

    def complete(self, _system_prompt, _user_prompt):
        self.usage_records.append(
            LLMUsage(input_tokens=12, output_tokens=8, cost_usd=0.01)
        )
        return json.dumps(
            {
                "issue_overview": (
                    "이 이슈는 공개 문서에 적힌 조건의 충족 여부를 정해진 기한 기준으로 추적합니다."
                ),
                "what_to_check": (
                    "게시된 조건 문구와 기준 시각 이후 공개 자료의 갱신 내용을 "
                    "추가로 확인해야 합니다."
                ),
            },
            ensure_ascii=False,
        )


def test_schema_to_verified_context_to_v4_api_flow(live_client, db_session):
    seed_basic_market(db_session)
    verifier = IndependentVerifierClient(
        IntegrationVerifierTransport(),
        "anthropic/verifier",
        research_model="openai/research",
    )

    context_outcomes = run_context_research_batch(
        db_session,
        NOW,
        IntegrationResearchClient(),
        verifier,
        clock=lambda: NOW,
    )
    assert context_outcomes[0].status == "success"
    assert context_outcomes[0].accepted_count == 1
    candidate = db_session.query(ContextCandidate).one()
    assert candidate.verification_state == "verified"
    assert db_session.query(ContextCollectionRun).one().status == "success"

    report_outcomes = run_v4_ai_report_batch(
        db_session,
        NOW,
        IntegrationWriterClient(),
        "openai/writer",
    )
    assert report_outcomes[0].status == "success"
    report = db_session.query(AiReport).filter_by(prompt_version="v4").one()
    assert report.content["evidence_refs"] == [
        "metric:1",
        f"candidate:{candidate.id}",
    ]

    response = live_client.get(f"/api/issues/{MARKET_ID}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["report_version"] == "v4"
    assert body["episode_at"].startswith("2026-07-08T09:00:00")
    assert body["evidence_refs"] == report.content["evidence_refs"]
    assert body["context_candidates"][0]["id"] == str(candidate.id)
    assert body["context_candidates"][0]["sources"] == [
        {
            "title": candidate.sources[0]["title"],
            "url": candidate.sources[0]["url"],
            "domain": candidate.sources[0]["domain"],
            "published_at": None,
            "source_type": "official",
        }
    ]
    assert "citation_id" not in body["context_candidates"][0]["sources"][0]
