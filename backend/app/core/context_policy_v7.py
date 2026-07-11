"""ADR-051 broad context classification and conditional verification.

The existing v4 verified-only path remains intact for historical rows. This
module consumes annotation-derived research results and classifies each exact
source as A, B, C, or rejected D without allowing a model to create provenance
or override deterministic failures.
"""

import json
import re
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, Literal, Protocol

from openai import OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchInputs,
    ResearchUsage,
)

V7_CONTEXT_POLICY_VERSION = "v7-source-level-1"
V7SourceLevel = Literal["A", "B", "C", "D"]

_WORD_PATTERN = re.compile(r"[A-Za-z0-9가-힣]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "will",
}
_DISALLOWED_DOMAINS = {
    "polymarket.com",
    "kalshi.com",
    "predictit.org",
    "metaculus.com",
    "manifold.markets",
}
_OFFICIAL_DOMAIN_MARKERS = (
    ".gov",
    ".gov.uk",
    ".go.kr",
    ".mil",
    "parliament.",
    "senate.",
    "court.",
    "europa.eu",
    "un.org",
)
_AMBIGUOUS_RELATIONSHIP_PATTERN = re.compile(
    r"\b(?:because|caused|drove|triggered|confirmed outcome)\b|"
    r"(?:때문에|원인|촉발|결과가\s*확정)",
    re.IGNORECASE,
)
_HIGH_IMPACT_PATTERN = re.compile(
    r"\b(?:resign(?:ed|ation)?|elected|declared|approved|enacted|ceased|"
    r"defaulted|invaded|signed)\b|(?:사임|당선|선언|승인|제정|발효|침공|서명)",
    re.IGNORECASE,
)


class V7ContextPolicyError(RuntimeError):
    """Raised for an invalid conditional-verifier configuration or response."""


class V7SupportedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ref: str = Field(min_length=3, max_length=220)
    text: str = Field(min_length=3, max_length=1200)
    excerpt: str = Field(min_length=3, max_length=4000)
    citation_id: str = Field(min_length=3, max_length=220)


class V7ClassifiedSource(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    citation_id: str
    title: str
    url: str
    canonical_url: str
    domain: str
    level: V7SourceLevel
    accepted: bool
    reason_code: str
    supported_claims: list[V7SupportedClaim] = Field(max_length=8)
    content_hash: str

    @model_validator(mode="after")
    def validate_public_shape(self) -> "V7ClassifiedSource":
        if self.level == "D" and (self.accepted or self.supported_claims):
            raise ValueError("Level D source cannot be accepted or expose claims")
        if self.level != "D" and (not self.accepted or not self.supported_claims):
            raise ValueError("Accepted A-C source requires supported claims")
        return self


class V7ClassifiedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate_key: str
    title: str
    event_at: Any
    matched_entities: list[str]
    matched_condition: str
    temporal_relation: Literal["before_window", "same_window", "after_window"]
    sources: list[V7ClassifiedSource]
    verifier_triggers: list[str]
    state: Literal["accepted", "withheld", "rejected"]
    reason_code: str

    @property
    def public_sources(self) -> list[V7ClassifiedSource]:
        return [source for source in self.sources if source.accepted]


class V7VerifierDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate_key: str
    accepted: bool
    supported_claim_refs: list[str]
    reason_code: str = Field(min_length=1, max_length=120)


class V7ConditionalVerifier(Protocol):
    model: str

    def verify(self, candidate: V7ClassifiedCandidate) -> V7VerifierDecision: ...


class ResearchClient(Protocol):
    model: str

    def research(self, inputs: ResearchInputs) -> ContextResearchResult: ...


def broaden_v7_research_inputs(
    inputs: ResearchInputs,
    *,
    lookback_days: int = 30,
) -> ResearchInputs:
    """Expand a change-episode input into bounded reusable issue context."""
    bounded_days = min(max(lookback_days, 1), 90)
    broad_start = min(
        inputs.search_window_start,
        inputs.search_window_end - timedelta(days=bounded_days),
    )
    return inputs.model_copy(
        update={
            "search_window_start": broad_start,
            "inflection_at": None,
        }
    )


class _ChatTransport(Protocol):
    @property
    def chat(self) -> Any: ...


def _tokens(*values: str) -> set[str]:
    return {
        token
        for token in _WORD_PATTERN.findall(" ".join(values).casefold())
        if len(token) >= 3 and token not in _STOPWORDS
    }


def _domain_matches(domain: str, allowed: str) -> bool:
    normalized = domain.casefold().rstrip(".")
    anchor = allowed.casefold().rstrip(".")
    return normalized == anchor or normalized.endswith(f".{anchor}")


def _is_official(domain: str, inputs: ResearchInputs) -> bool:
    if any(_domain_matches(domain, allowed) for allowed in inputs.allowed_domains):
        return True
    normalized = domain.casefold()
    return any(marker in normalized for marker in _OFFICIAL_DOMAIN_MARKERS)


def _source_level(
    citation: NormalizedCitation,
    inputs: ResearchInputs,
    established_domains: set[str],
) -> V7SourceLevel:
    if any(_domain_matches(citation.domain, blocked) for blocked in _DISALLOWED_DOMAINS):
        return "D"
    if not citation.content_excerpt.strip():
        return "D"
    if _is_official(citation.domain, inputs):
        return "A"
    if any(_domain_matches(citation.domain, domain) for domain in established_domains):
        return "B"
    return "C"


def _claim_for_source(
    candidate: ResearchCandidateDraft,
    citation: NormalizedCitation,
) -> V7SupportedClaim | None:
    # A title can establish topical relevance, but only the stored excerpt can
    # support a public factual claim.
    evidence_tokens = _tokens(citation.content_excerpt)
    claim_text = candidate.matched_condition.strip() or candidate.title.strip()
    claim_tokens = _tokens(claim_text, *candidate.matched_entities)
    overlap = evidence_tokens & claim_tokens
    if not overlap:
        return None
    return V7SupportedClaim(
        ref=f"claim:{candidate.candidate_key}:{citation.citation_id.partition(':')[2][:16]}",
        text=claim_text,
        excerpt=citation.content_excerpt,
        citation_id=citation.citation_id,
    )


def classify_v7_candidate(
    candidate: ResearchCandidateDraft,
    citations_by_id: Mapping[str, NormalizedCitation],
    inputs: ResearchInputs,
    *,
    established_domains: set[str] | None = None,
    material_to_summary: bool = False,
    conflicting_citation_ids: set[str] | None = None,
) -> V7ClassifiedCandidate:
    """Classify exact annotation sources and derive conditional triggers."""
    established = {domain.casefold() for domain in (established_domains or set())}
    conflicts = conflicting_citation_ids or set()
    sources: list[V7ClassifiedSource] = []
    triggers: set[str] = set()

    for citation_id in dict.fromkeys(candidate.citation_ids):
        citation = citations_by_id.get(citation_id)
        if citation is None:
            continue
        level = _source_level(citation, inputs, established)
        claim = _claim_for_source(candidate, citation) if level != "D" else None
        if level == "D":
            reason = "source_rejected"
        elif claim is None:
            level = "D"
            reason = "claim_not_supported_by_excerpt"
        else:
            reason = f"accepted_level_{level.lower()}"
        source = V7ClassifiedSource(
            citation_id=citation.citation_id,
            title=citation.title,
            url=citation.url,
            canonical_url=citation.canonical_url,
            domain=citation.domain,
            level=level,
            accepted=level != "D",
            reason_code=reason,
            supported_claims=[claim] if claim is not None else [],
            content_hash=citation.content_hash,
        )
        sources.append(source)
        if citation_id in conflicts:
            triggers.add("source_conflict")
        if source.accepted and level in {"B", "C"}:
            combined = f"{candidate.title} {candidate.matched_condition} {citation.content_excerpt}"
            if _AMBIGUOUS_RELATIONSHIP_PATTERN.search(combined):
                triggers.add("strong_relationship_language")
            if _HIGH_IMPACT_PATTERN.search(combined):
                triggers.add("high_impact_claim")
        if source.accepted and level == "C" and material_to_summary:
            triggers.add("material_level_c_claim")

    public_sources = [source for source in sources if source.accepted]
    if not public_sources:
        return V7ClassifiedCandidate(
            candidate_key=candidate.candidate_key,
            title=candidate.title,
            event_at=candidate.event_at,
            matched_entities=candidate.matched_entities,
            matched_condition=candidate.matched_condition,
            temporal_relation=candidate.temporal_relation,
            sources=sources,
            verifier_triggers=sorted(triggers),
            state="rejected",
            reason_code="no_supported_source",
        )
    return V7ClassifiedCandidate(
        candidate_key=candidate.candidate_key,
        title=candidate.title,
        event_at=candidate.event_at,
        matched_entities=candidate.matched_entities,
        matched_condition=candidate.matched_condition,
        temporal_relation=candidate.temporal_relation,
        sources=sources,
        verifier_triggers=sorted(triggers),
        state="withheld" if triggers else "accepted",
        reason_code="conditional_verifier_required" if triggers else "deterministic_checks_passed",
    )


def _model_family(model: str) -> str:
    normalized = model.casefold().strip()
    return normalized.split("/", 1)[0] if "/" in normalized else normalized.split("-", 1)[0]


def apply_v7_conditional_verifier(
    candidate: V7ClassifiedCandidate,
    verifier: V7ConditionalVerifier | None,
    *,
    research_model: str,
) -> V7ClassifiedCandidate:
    """Run the verifier only for triggered A-C candidates, failing closed."""
    if candidate.state == "rejected" or not candidate.verifier_triggers:
        return candidate
    if verifier is None:
        return candidate.model_copy(
            update={"state": "withheld", "reason_code": "verifier_unavailable"}
        )
    if _model_family(verifier.model) == _model_family(research_model):
        raise V7ContextPolicyError("Conditional verifier must use an independent provider family")
    decision = verifier.verify(candidate)
    if decision.candidate_key != candidate.candidate_key:
        raise V7ContextPolicyError("Conditional verifier candidate key mismatch")
    allowed_refs = {
        claim.ref for source in candidate.public_sources for claim in source.supported_claims
    }
    if not set(decision.supported_claim_refs).issubset(allowed_refs):
        raise V7ContextPolicyError("Conditional verifier returned an unknown claim ref")
    if not decision.accepted:
        return candidate.model_copy(
            update={"state": "withheld", "reason_code": decision.reason_code}
        )
    return candidate.model_copy(
        update={"state": "accepted", "reason_code": "conditional_verifier_passed"}
    )


class OpenRouterV7ConditionalVerifier:
    """No-search strict verifier for only the candidates routed by policy."""

    def __init__(self, client: _ChatTransport, model: str) -> None:
        self._client = client
        self.model = model

    def verify(self, candidate: V7ClassifiedCandidate) -> V7VerifierDecision:
        evidence = [
            {
                "claim_ref": claim.ref,
                "claim": claim.text,
                "excerpt": claim.excerpt,
                "source_title": source.title,
                "source_domain": source.domain,
                "source_level": source.level,
            }
            for source in candidate.public_sources
            for claim in source.supported_claims
        ]
        payload = {
            "candidate_key": candidate.candidate_key,
            "title": candidate.title,
            "triggers": candidate.verifier_triggers,
            "evidence": evidence,
        }
        kwargs = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Verify only whether the candidate is supported by the supplied exact "
                        "excerpts. Do not browse or add facts. Return JSON with candidate_key, "
                        "accepted, supported_claim_refs, and reason_code."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "timeout": 30,
        }
        try:
            response = self._client.chat.completions.create(**kwargs)
        except (OpenAIError, TimeoutError) as exc:
            raise V7ContextPolicyError(
                f"Conditional verifier failed: {type(exc).__name__}"
            ) from exc
        if not response.choices or not response.choices[0].message.content:
            raise V7ContextPolicyError("Conditional verifier returned no content")
        try:
            return V7VerifierDecision.model_validate_json(response.choices[0].message.content)
        except ValidationError as exc:
            raise V7ContextPolicyError("Conditional verifier returned invalid JSON") from exc


class V7ContextCollectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: Literal["v7-source-level-1"] = V7_CONTEXT_POLICY_VERSION
    research_model: str
    queries: list[str]
    candidates: list[V7ClassifiedCandidate]
    usage: ResearchUsage

    @property
    def accepted(self) -> list[V7ClassifiedCandidate]:
        return [candidate for candidate in self.candidates if candidate.state == "accepted"]


def collect_v7_context(
    inputs: ResearchInputs,
    research_client: ResearchClient,
    *,
    established_domains: set[str] | None = None,
    verifier: V7ConditionalVerifier | None = None,
    material_candidate_keys: set[str] | None = None,
    conflicting_citation_ids: set[str] | None = None,
) -> V7ContextCollectionResult:
    """Research broadly, classify exact annotations, and verify only triggers."""
    research_inputs = broaden_v7_research_inputs(inputs)
    research = research_client.research(research_inputs)
    citations = {citation.citation_id: citation for citation in research.citations}
    material_keys = material_candidate_keys or set()
    candidates = []
    for draft in research.candidates:
        classified = classify_v7_candidate(
            draft,
            citations,
            research_inputs,
            established_domains=established_domains,
            material_to_summary=draft.candidate_key in material_keys,
            conflicting_citation_ids=conflicting_citation_ids,
        )
        candidates.append(
            apply_v7_conditional_verifier(
                classified,
                verifier,
                research_model=research.model,
            )
        )
    return V7ContextCollectionResult(
        research_model=research.model,
        queries=research.queries,
        candidates=candidates,
        usage=research.usage,
    )
