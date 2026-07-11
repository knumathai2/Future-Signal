"""Deterministic and independent-AI verification for v4 context (TASK-059).

The verifier model can only withhold a candidate that passed deterministic
checks; it can never promote a hard-gate failure. The verifier receives stored
annotation evidence and normalized candidate fields only, with no web-search
tool and no database access.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Literal, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import OPENROUTER_BASE_URL, Settings
from app.core.context_research import (
    ContextResearchResult,
    NormalizedCitation,
    ResearchCandidateDraft,
    ResearchInputs,
)

MAX_RULE_PASSING_CANDIDATES = 8
MAX_VERIFIER_CANDIDATES = 5
VERIFICATION_POLICY_VERSION = "v4"

_TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"}
_UNSAFE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bbecause\b",
        r"\bdue to\b",
        r"\bcaused by\b",
        r"\bexplains? the (?:change|movement)\b",
        r"\bwill (?:happen|occur|win|lose)\b",
        r"\bthe outcome (?:is|was) (?:confirmed|certain)\b",
        r"\brecommend(?:ed|ation)?\b",
        r"때문에",
        r"로 인해",
        r"원인(?:이다|입니다|으로)",
        r"(?:현실의\s*)?결과(?:가|는).*?(?:확정|입증|발생|실현)",
        r"추천",
    )
)
_MONTH_FORMATS = ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y")
_MONTH_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b|"
    r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
    re.IGNORECASE,
)
_ISO_DATE_PATTERN = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
_WORD_PATTERN = re.compile(r"[A-Za-z0-9가-힣]+")
_PROPER_NOUN_PATTERN = re.compile(r"\b(?:[A-Z][A-Za-z0-9&.-]+(?:\s+|$)){1,4}")
_PROPER_NOUN_STOPWORDS = {
    "Official",
    "Public",
    "Source",
    "Update",
    "Recorded",
    "Report",
    "Statement",
    "The",
}
_TOKEN_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "will",
}
_MULTIPART_PUBLIC_SUFFIXES = {
    "co.jp",
    "co.kr",
    "co.uk",
    "com.au",
    "com.br",
    "com.mx",
    "gov.au",
    "gov.uk",
    "org.uk",
}
_DISALLOWED_MARKET_DOMAINS = {
    "polymarket.com",
    "kalshi.com",
    "predictit.org",
    "metaculus.com",
    "manifold.markets",
}


class ContextVerificationError(RuntimeError):
    """Raised for verifier configuration, provider, or schema failures."""


class VerifiedSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    title: str
    url: str
    canonical_url: str
    domain: str
    source_type: Literal["official", "independent_secondary"]
    content_hash: str


class DeterministicGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    passed: bool
    reason_code: str
    sources: list[VerifiedSource] = Field(default_factory=list)


class _VerifierEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    title: str
    url: str
    domain: str
    content_excerpt: str


class _VerifierCandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    title: str
    event_at: datetime
    matched_entities: list[str]
    matched_condition: str
    evidence: list[_VerifierEvidence]


class VerifierOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidate_key: str
    accepted: bool
    condition_match: bool
    date_match: bool
    source_supported: bool
    unsupported_claims: list[str]
    conflicting_citation_ids: list[str]
    neutral_summary_ko: str = Field(min_length=1, max_length=700)
    reason_code: str = Field(min_length=1)

    @field_validator("neutral_summary_ko")
    @classmethod
    def limit_summary_sentences(cls, value: str) -> str:
        sentence_count = len(re.findall(r"[.!?]+(?=\s|$)", value.strip())) or 1
        if sentence_count > 2:
            raise ValueError("Verifier summary must contain at most two sentences")
        return value


class _VerifierResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verifications: list[VerifierOutput] = Field(max_length=MAX_VERIFIER_CANDIDATES)


class VerificationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_key: str
    verification_state: Literal["verified", "withheld", "rejected"]
    reason_code: str
    neutral_summary_ko: str | None
    sources: list[VerifiedSource]
    evidence_hash: str | None
    research_model: str
    verifier_model: str
    policy_version: Literal["v4"] = VERIFICATION_POLICY_VERSION


class ContextVerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisions: list[VerificationDecision]

    @property
    def verified(self) -> list[VerificationDecision]:
        return [item for item in self.decisions if item.verification_state == "verified"]


class VerifierUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None


class ChatCompletionsTransport(Protocol):
    @property
    def chat(self) -> Any: ...


def canonicalize_url(url: str) -> str | None:
    """Return a stable HTTP(S) URL or ``None`` for unsafe/invalid input."""
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password:
        return None

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower().rstrip(".")
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = host if port is None or default_port else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
    ]
    return urlunsplit((scheme, netloc, path, urlencode(sorted(query)), ""))


def _normalized_text(value: str) -> str:
    return " ".join(_WORD_PATTERN.findall(value.casefold()))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _WORD_PATTERN.findall(value.casefold())
        if len(token) > 1 and token not in _TOKEN_STOPWORDS
    }


def _overlap_ratio(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    if not left_tokens:
        return 0.0
    return len(left_tokens & _tokens(right)) / len(left_tokens)


def _extract_dates(value: str) -> set[str]:
    dates = set(_ISO_DATE_PATTERN.findall(value))
    for match in _MONTH_PATTERN.findall(value):
        for date_format in _MONTH_FORMATS:
            try:
                dates.add(datetime.strptime(match, date_format).date().isoformat())
                break
            except ValueError:
                continue
    return dates


def _proper_nouns(value: str) -> set[str]:
    nouns: set[str] = set()
    for match in _PROPER_NOUN_PATTERN.findall(value):
        cleaned = " ".join(match.split()).strip(" .")
        if cleaned and cleaned not in _PROPER_NOUN_STOPWORDS:
            nouns.add(cleaned)
    return nouns


def _source_family(domain: str) -> str:
    normalized = domain.casefold().removeprefix("www.")
    labels = normalized.split(".")
    if len(labels) <= 2:
        return normalized
    suffix2 = ".".join(labels[-2:])
    if suffix2 in _MULTIPART_PUBLIC_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return suffix2


def _is_official_domain(domain: str, inputs: ResearchInputs) -> bool:
    normalized = domain.casefold().removeprefix("www.")
    configured = {item.casefold().removeprefix("www.") for item in inputs.allowed_domains}
    if inputs.resolution_source:
        canonical = canonicalize_url(inputs.resolution_source)
        if canonical:
            configured.add(urlsplit(canonical).hostname or "")
    if any(normalized == item or normalized.endswith(f".{item}") for item in configured):
        return True
    labels = set(normalized.split("."))
    return bool(labels & {"gov", "mil"}) or normalized.endswith(".int")


def _is_disallowed_market_or_forecast_page(domain: str) -> bool:
    normalized = domain.casefold().removeprefix("www.")
    return any(
        normalized == blocked or normalized.endswith(f".{blocked}")
        for blocked in _DISALLOWED_MARKET_DOMAINS
    )


def _contains_unsafe_language(*values: str) -> bool:
    text = "\n".join(values)
    return any(pattern.search(text) for pattern in _UNSAFE_PATTERNS)


def _normalized_sources(
    citations: Sequence[NormalizedCitation], inputs: ResearchInputs
) -> list[VerifiedSource] | None:
    sources: list[VerifiedSource] = []
    seen_urls: set[str] = set()
    for citation in citations:
        canonical = canonicalize_url(citation.url)
        if not canonical:
            return None
        if canonical in seen_urls:
            continue
        seen_urls.add(canonical)
        domain = urlsplit(canonical).hostname or ""
        sources.append(
            VerifiedSource(
                citation_id=citation.citation_id,
                title=citation.title,
                url=citation.url,
                canonical_url=canonical,
                domain=domain,
                source_type=(
                    "official" if _is_official_domain(domain, inputs) else "independent_secondary"
                ),
                content_hash=citation.content_hash,
            )
        )
    return sources


def deterministic_gate(
    inputs: ResearchInputs,
    candidate: ResearchCandidateDraft,
    citations: Sequence[NormalizedCitation],
) -> DeterministicGateResult:
    """Apply non-model provenance, date, entity, condition, and source gates."""
    if candidate.event_at is None:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="missing_event_date",
        )
    if not inputs.search_window_start <= candidate.event_at <= inputs.search_window_end:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="event_date_outside_window",
        )
    if _contains_unsafe_language(candidate.title, candidate.matched_condition):
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="unsafe_relationship_language",
        )

    citations_by_id = {citation.citation_id: citation for citation in citations}
    selected = [citations_by_id[item] for item in candidate.citation_ids if item in citations_by_id]
    if len(selected) != len(set(candidate.citation_ids)) or not selected:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="missing_annotation_evidence",
        )
    sources = _normalized_sources(selected, inputs)
    if sources is None:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="invalid_source_url",
        )
    if any(_is_disallowed_market_or_forecast_page(source.domain) for source in sources):
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="market_or_forecast_page",
            sources=sources,
        )

    market_text = " ".join(
        (inputs.title, inputs.description, inputs.tracked_condition, inputs.category)
    )
    evidence_texts = {
        citation.citation_id: f"{citation.title} {citation.content_excerpt}"
        for citation in selected
    }
    evidence_corpus = " ".join(evidence_texts.values())
    if not candidate.matched_entities:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="missing_matched_entity",
        )
    for entity in candidate.matched_entities:
        normalized_entity = _normalized_text(entity)
        if (
            not normalized_entity
            or normalized_entity not in _normalized_text(market_text)
            or normalized_entity not in _normalized_text(evidence_corpus)
        ):
            return DeterministicGateResult(
                candidate_key=candidate.candidate_key,
                passed=False,
                reason_code="entity_mismatch",
            )

    if _overlap_ratio(candidate.matched_condition, inputs.tracked_condition) < 0.6:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="condition_mismatch",
        )

    unsupported_nouns = {
        noun
        for noun in _proper_nouns(candidate.title)
        if _normalized_text(noun) not in _normalized_text(f"{market_text} {evidence_corpus}")
    }
    if unsupported_nouns:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="unsupported_proper_noun",
        )

    candidate_date = candidate.event_at.date().isoformat()
    direct_source_ids: list[str] = []
    conflicting_ids: list[str] = []
    for citation in selected:
        text = evidence_texts[citation.citation_id]
        dates = _extract_dates(text)
        if dates and candidate_date not in dates:
            conflicting_ids.append(citation.citation_id)
            continue
        entity_supported = all(
            _normalized_text(entity) in _normalized_text(text)
            for entity in candidate.matched_entities
        )
        condition_supported = _overlap_ratio(candidate.matched_condition, text) >= 0.6
        if candidate_date in dates and entity_supported and condition_supported:
            direct_source_ids.append(citation.citation_id)
    if conflicting_ids:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="conflicting_source_date",
            sources=sources,
        )

    direct_sources = [source for source in sources if source.citation_id in direct_source_ids]
    official_path = any(source.source_type == "official" for source in direct_sources)
    independent_sources = [
        source for source in direct_sources if source.source_type == "independent_secondary"
    ]
    independent_families = {_source_family(source.domain) for source in independent_sources}
    selected_by_id = {citation.citation_id: citation for citation in selected}
    independent_hashes = {source.content_hash for source in independent_sources}
    independent_fingerprints = {
        _normalized_text(selected_by_id[source.citation_id].content_excerpt)
        for source in independent_sources
    }
    independent_path = (
        len(independent_families) >= 2
        and len(independent_hashes) >= 2
        and len(independent_fingerprints) >= 2
    )
    if not official_path and not independent_path:
        return DeterministicGateResult(
            candidate_key=candidate.candidate_key,
            passed=False,
            reason_code="insufficient_independent_sources",
            sources=sources,
        )
    return DeterministicGateResult(
        candidate_key=candidate.candidate_key,
        passed=True,
        reason_code="official_direct_match" if official_path else "independent_multi_source_match",
        sources=sources,
    )


def _evidence_hash(candidate: ResearchCandidateDraft, sources: Sequence[VerifiedSource]) -> str:
    payload = {
        "candidate_key": candidate.candidate_key,
        "event_at": candidate.event_at.isoformat() if candidate.event_at else None,
        "sources": sorted(
            (source.canonical_url, source.content_hash, source.citation_id) for source in sources
        ),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _model_family(model: str) -> str:
    return model.split("/", 1)[0].casefold()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    data = getattr(value, "__dict__", None)
    return data if isinstance(data, Mapping) else {}


def _parse_verifier_usage(raw_usage: Any) -> VerifierUsage:
    usage = _as_mapping(raw_usage)
    cost = usage.get("cost")
    return VerifierUsage(
        input_tokens=int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or usage.get("output_tokens") or 0),
        cost_usd=float(cost) if cost is not None else None,
    )


class IndependentVerifierClient:
    """One-call verifier using a provider family distinct from research."""

    def __init__(
        self,
        client: ChatCompletionsTransport,
        model: str,
        *,
        research_model: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        if (
            not model
            or model == research_model
            or _model_family(model) == _model_family(research_model)
        ):
            raise ContextVerificationError(
                "Verifier model must use a different provider family from research"
            )
        self._client = client
        self.model = model
        self._extra_headers = extra_headers or {}
        self.last_usage = VerifierUsage()

    def verify(self, candidates: Sequence[_VerifierCandidateInput]) -> list[VerifierOutput]:
        payload = [candidate.model_dump(mode="json") for candidate in candidates]
        prompt = (
            "Check each candidate only against its supplied annotation evidence. "
            "Do not search the web. Do not add URLs, dates, entities, causes, or results. "
            "Return strict JSON with a verifications array using exactly: candidate_key, "
            "accepted, condition_match, date_match, source_supported, unsupported_claims, "
            "conflicting_citation_ids, neutral_summary_ko, reason_code.\n"
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You independently verify source support. Evidence limits are binding. "
                        "Never infer a relationship with the observed data movement."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "timeout": 30,
        }
        if self._extra_headers:
            kwargs["extra_headers"] = self._extra_headers
        try:
            response = self._client.chat.completions.create(**kwargs)
        except (OpenAIError, TimeoutError) as exc:
            raise ContextVerificationError(
                f"Independent verifier failed: {type(exc).__name__}"
            ) from exc
        if not response.choices or not response.choices[0].message.content:
            raise ContextVerificationError("Independent verifier returned empty content")
        try:
            parsed = _VerifierResponse.model_validate_json(response.choices[0].message.content)
        except ValidationError as exc:
            raise ContextVerificationError("Independent verifier returned invalid JSON") from exc
        self.last_usage = _parse_verifier_usage(getattr(response, "usage", None))
        return parsed.verifications


def verify_research_result(
    inputs: ResearchInputs,
    research: ContextResearchResult,
    verifier: IndependentVerifierClient,
) -> ContextVerificationResult:
    """Run deterministic gates, then one independent verifier call for at most five."""
    decisions: list[VerificationDecision] = []
    candidate_keys = [candidate.candidate_key for candidate in research.candidates]
    if len(candidate_keys) != len(set(candidate_keys)):
        raise ContextVerificationError("Research returned duplicate candidate keys")
    candidate_by_key = {candidate.candidate_key: candidate for candidate in research.candidates}
    gate_by_key: dict[str, DeterministicGateResult] = {}
    rule_passing: list[ResearchCandidateDraft] = []

    for candidate in research.candidates:
        gate = deterministic_gate(inputs, candidate, research.citations)
        gate_by_key[candidate.candidate_key] = gate
        if not gate.passed:
            decisions.append(
                VerificationDecision(
                    candidate_key=candidate.candidate_key,
                    verification_state="rejected",
                    reason_code=gate.reason_code,
                    neutral_summary_ko=None,
                    sources=gate.sources,
                    evidence_hash=_evidence_hash(candidate, gate.sources),
                    research_model=research.model,
                    verifier_model=verifier.model,
                )
            )
        elif len(rule_passing) < MAX_RULE_PASSING_CANDIDATES:
            rule_passing.append(candidate)
        else:
            decisions.append(
                VerificationDecision(
                    candidate_key=candidate.candidate_key,
                    verification_state="withheld",
                    reason_code="rule_passing_candidate_limit",
                    neutral_summary_ko=None,
                    sources=gate.sources,
                    evidence_hash=_evidence_hash(candidate, gate.sources),
                    research_model=research.model,
                    verifier_model=verifier.model,
                )
            )

    verifier_candidates = rule_passing[:MAX_VERIFIER_CANDIDATES]
    for candidate in rule_passing[MAX_VERIFIER_CANDIDATES:]:
        gate = gate_by_key[candidate.candidate_key]
        decisions.append(
            VerificationDecision(
                candidate_key=candidate.candidate_key,
                verification_state="withheld",
                reason_code="verifier_candidate_limit",
                neutral_summary_ko=None,
                sources=gate.sources,
                evidence_hash=_evidence_hash(candidate, gate.sources),
                research_model=research.model,
                verifier_model=verifier.model,
            )
        )

    if verifier_candidates:
        verifier_inputs = [
            _VerifierCandidateInput(
                candidate_key=candidate.candidate_key,
                title=candidate.title,
                event_at=candidate.event_at,
                matched_entities=candidate.matched_entities,
                matched_condition=candidate.matched_condition,
                evidence=[
                    _VerifierEvidence(
                        citation_id=citation.citation_id,
                        title=citation.title,
                        url=citation.url,
                        domain=citation.domain,
                        content_excerpt=citation.content_excerpt,
                    )
                    for citation in research.citations
                    if citation.citation_id in candidate.citation_ids
                ],
            )
            for candidate in verifier_candidates
            if candidate.event_at is not None
        ]
        outputs = verifier.verify(verifier_inputs)
        output_by_key = {output.candidate_key: output for output in outputs}
        if len(output_by_key) != len(outputs):
            raise ContextVerificationError("Verifier returned duplicate candidate keys")
        expected_keys = {candidate.candidate_key for candidate in verifier_candidates}
        if set(output_by_key) != expected_keys:
            raise ContextVerificationError("Verifier returned a mismatched candidate set")

        for candidate in verifier_candidates:
            gate = gate_by_key[candidate.candidate_key]
            output = output_by_key.get(candidate.candidate_key)
            if output is None:
                decisions.append(
                    VerificationDecision(
                        candidate_key=candidate.candidate_key,
                        verification_state="withheld",
                        reason_code="verifier_missing_candidate",
                        neutral_summary_ko=None,
                        sources=gate.sources,
                        evidence_hash=_evidence_hash(candidate, gate.sources),
                        research_model=research.model,
                        verifier_model=verifier.model,
                    )
                )
                continue

            evidence_text = " ".join(
                f"{citation.title} {citation.content_excerpt}"
                for citation in research.citations
                if citation.citation_id in candidate.citation_ids
            )
            summary_dates = _extract_dates(output.neutral_summary_ko)
            evidence_dates = _extract_dates(evidence_text)
            summary_nouns = _proper_nouns(output.neutral_summary_ko)
            unsupported_nouns = {
                noun
                for noun in summary_nouns
                if _normalized_text(noun)
                not in _normalized_text(f"{inputs.title} {inputs.description} {evidence_text}")
            }
            accepted = (
                output.accepted
                and output.condition_match
                and output.date_match
                and output.source_supported
                and not output.unsupported_claims
                and not output.conflicting_citation_ids
                and not _contains_unsafe_language(output.neutral_summary_ko)
                and summary_dates.issubset(evidence_dates)
                and not unsupported_nouns
            )
            decisions.append(
                VerificationDecision(
                    candidate_key=candidate.candidate_key,
                    verification_state="verified" if accepted else "withheld",
                    reason_code=output.reason_code if accepted else "independent_verifier_rejected",
                    neutral_summary_ko=output.neutral_summary_ko if accepted else None,
                    sources=gate.sources,
                    evidence_hash=_evidence_hash(
                        candidate_by_key[candidate.candidate_key], gate.sources
                    ),
                    research_model=research.model,
                    verifier_model=verifier.model,
                )
            )

    order = {candidate.candidate_key: index for index, candidate in enumerate(research.candidates)}
    decisions.sort(key=lambda decision: order[decision.candidate_key])
    return ContextVerificationResult(decisions=decisions)


def build_independent_verifier_client(
    api_key: str,
    model: str,
    *,
    research_model: str,
    extra_headers: dict[str, str] | None = None,
) -> IndependentVerifierClient:
    return IndependentVerifierClient(
        OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL),
        model,
        research_model=research_model,
        extra_headers=extra_headers,
    )


def build_independent_verifier_from_settings(
    app_settings: Settings,
) -> IndependentVerifierClient:
    key = app_settings.openrouter_api_key
    if not key and app_settings.openai_api_key and app_settings.openai_api_key.startswith("sk-or-"):
        key = app_settings.openai_api_key
    if not key:
        raise ContextVerificationError("OpenRouter API key is not configured")
    if not app_settings.context_verifier_model:
        raise ContextVerificationError("Independent verifier model is not configured")
    headers: dict[str, str] = {}
    if app_settings.openrouter_http_referer:
        headers["HTTP-Referer"] = app_settings.openrouter_http_referer
    if app_settings.openrouter_app_title:
        headers["X-OpenRouter-Title"] = app_settings.openrouter_app_title
    return build_independent_verifier_client(
        key,
        app_settings.context_verifier_model,
        research_model=app_settings.context_research_model,
        extra_headers=headers,
    )
