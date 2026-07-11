# Technical Design: Metrics, Signals, AI Report Architecture

_Source: former project-root Technical Design sections 7-10._

---

## 7. Metric Calculation Flow

(Detailed formulas already defined in Service Design §5 — this section is the engineering sequencing.)

1. For each market, pull the last N `market_snapshots` covering the widest window needed (30d if available, else whatever history exists).
2. Compute `change_24h` = `price(now) - price(now-24h)` (nearest available snapshot to that time), same pattern for `change_7d`.
3. If volatility/attention are in scope for the current build day (P1), compute them from the same pulled window — no separate query needed.
4. Compute `confidence_level` from volume, liquidity, and market age against fixed thresholds (define initial thresholds as constants, e.g., `min_volume_24h`, `min_snapshots_required` — expect to tune these once real data is seen on Day 2 of the hackathon, per PRD's Day 2 plan).
5. Compute `heat_score` as a simple weighted sum for MVP (e.g., `abs(change_24h) * 0.6 + normalized_volume * 0.4`) — do not over-engineer this formula before seeing real data; it only needs to produce a sensible top-10 ranking for the demo, not a validated model.
6. Upsert (insert new row) into `market_metrics`.

---

## 8. Sudden Change Signal Detection Flow

1. After metrics are computed for a market, check `abs(change_24h) >= threshold` (default 5pp, matching PRD §8.6).
2. Check whether an unresolved signal of the same type already exists for this market within the current window (cooldown check) — if so, skip to avoid duplicate/spammy signals.
3. If triggered and not a duplicate, classify severity (Section 5 badge tiers from Service Design §7 — MVP only needs to support `medium`, since only the single threshold-based "Expectation Shift Detected" signal is in scope).
4. Insert into `issue_signals`.
5. This is also exactly the trigger condition feeding batch step 8 (AI report regeneration) — a new signal is one of the three conditions that qualifies a market for report regeneration.

---

## 9. AI Report Generation Architecture

```
market_metrics (latest) + market_snapshots (window) + related_events (if any)
                    |
                    v
        build_prompt() -- fills a fixed template, never free text
                    |
                    v
        call LLM API (Claude or OpenAI)
                    |
                    v
        parse structured response into fixed sections
                    |
                    v
        run banned-phrase safety filter (UX Design §5.3 list)
                    |
              pass?  |  fail?
              v            v
        store in        discard, log failure,
        ai_reports       keep previous report live
```

### Regeneration conditions (cost control, per batch step 8)
A market qualifies for regeneration only if **any** of:
- A new `issue_signals` row fired for it this run, or
- It has no `ai_reports` row yet, or
- Its most recent report is older than a staleness threshold (recommend 24h for MVP).

And is capped at a **maximum reports per batch run** (e.g., top 10 by `heat_score` among qualifying markets) so a bad day of many signals firing at once can't blow the API budget.

### Cost-control strategy
- Template-constrained prompts (below) keep both input and output token counts small and predictable — no open-ended "analyze this market" prompt.
- Regenerate only on meaningful change, never on a fixed short interval regardless of data movement.
- Cap reports per run.
- Reuse (serve the existing row from `ai_reports`) whenever a market doesn't qualify for regeneration — the API layer never calls the LLM live.

---

## 10. AI Prompt and Output Design

### 10.1 System prompt (fixed, never modified per-request)
```
You are generating a short, neutral issue explainer for a public
issue-monitoring dashboard. Write in clear Korean for non-specialist readers.
You are explaining the market question and the public data context, not
predicting real-world outcomes and not giving advice of any kind.

Rules you must always follow:
- Explain the issue in plain language before mentioning the data reading.
- Use scenario sections only as conditional explanations of what the market
  question would mean if that condition is confirmed, limited, or not confirmed.
- Never label a scenario as best, worst, good, bad, desirable, or undesirable.
- Never state or imply that an outcome will or will not happen.
- Never use: bet, buy, sell, trade, position, long, short, profit, win rate,
  recommend, guaranteed, best pick, follow, copy, opportunity.
- Never suggest any action the reader should take.
- Never use causal connectors such as "because", "due to", or "caused by".
- If a related event candidate is provided, describe it only as a "candidate
  for context," never as a cause.
- If data is limited (low volume, short history, high volatility), say so
  plainly instead of writing around it.
- Keep every section to 1-3 sentences.
```

### 10.2 User/task prompt template
```
Market title: {{title}}
Market description: {{description}}
Category: {{category}}
Current expectation value: {{current_value}}
24h change: {{change_24h}}
7d change: {{change_7d}}
Confidence level: {{confidence_level}}
Recent inflection point (if any): {{inflection_point_summary}}
Related event candidate (if any): {{related_event_or_none}}

Produce a JSON object in Korean with exactly these fields:
{
  "issue_explainer": "...",
  "why_it_matters": "...",
  "current_reading": "...",
  "scenario_major_change": "...",
  "scenario_limited_change": "...",
  "scenario_status_quo": "...",
  "check_points": "...",
  "caution_note": "..."
}
```

### 10.3 Example output (stored in `ai_reports.content` as jsonb)
```json
{
  "issue_explainer": "이 이슈는 기준일까지 특정 조건이 확인되는지를 공개 데이터 맥락에서 살펴보는 항목입니다.",
  "why_it_matters": "해당 조건은 관련 기관의 일정, 정책 논의, 후속 절차를 이해하는 데 참고 맥락이 될 수 있습니다.",
  "current_reading": "현재 공개 데이터에서는 이 이슈가 일부 재평가되고 있으나, 실제 결과를 뜻하지는 않습니다.",
  "scenario_major_change": "조건이 명확히 성립하는 경우, 관련 절차가 확인되며 후속 논의가 더 중요해질 수 있습니다.",
  "scenario_limited_change": "관련 논의는 이어지지만 조건이 일부만 충족되는 경우, 실제 변화는 제한적일 수 있습니다.",
  "scenario_status_quo": "조건이 성립하지 않는 경우, 기존 일정이나 제도가 대체로 유지되는 상황으로 해석할 수 있습니다.",
  "check_points": "확인할 지점은 공식 발표, 기준일, 후속 절차의 진행 여부입니다.",
  "caution_note": "이 요약은 공개 데이터와 등록된 맥락을 정리한 것이며, 실제 결과에 대한 전망이나 행동 제안이 아닙니다."
}
```

### 10.4 Safety filter (runs after every generation, before storage)
1. Lowercase the full concatenated output and check against the prohibited-word list from UX Design §5.3 (bet, buy, sell, trade, position, long, short, profit, win rate, copy trader, follow, expert trader, best pick, recommended outcome, high-return, guaranteed).
2. Check for a small set of banned sentence patterns (regex) such as `"will (happen|occur)"`, `"you should"`, `"recommend"`.
3. If any check fails: discard the output, log the failure (which rule, which market) to `data_collection_logs` or a dedicated error log, keep the previous `ai_reports` row as the one served, and do **not** retry with the same prompt automatically — a failing generation likely indicates a prompt issue worth a human look, not a transient error.
4. If checks pass: store with `status = success`.

### 10.5 Report storage and regeneration
Already covered in Sections 4.6 and 9 — one row per generation event, never overwritten in place, so `ai_reports` doubles as a natural audit trail of how the summary changed over time if that's ever useful.

### 10.6 Error handling
- LLM API timeout/error → one retry, then `status = failed`, previous good report stays live.
- Malformed JSON in response → treat as a failure the same way (don't attempt partial parsing under time pressure).

### 10.7 Approved v4 evidence contract (ADR-038)

V4 generation receives only the latest stored metric/snapshot evidence and
stored `verified` context candidates. Its content object has exactly seven
keys: `issue_overview`, `observed_change`, nullable `context_summary`,
`relationship_boundary`, `what_to_check`, `data_limitations`, and
`caution_note`. Top-level output adds `report_version="v4"`, report/data/episode
timing, `evidence_refs`, and verified context candidates with public source
metadata.

Every numeric statement must resolve to a stored `metric:<id>` reference and
match that metric. Every context statement must resolve to a stored
`candidate:<uuid>` whose state is `verified` and whose source URLs match stored
OpenRouter citation annotations. Missing/extra fields, invented values,
unknown evidence IDs, absent sources, missing relationship-boundary copy,
unsafe wording, or inconsistent timing block storage and public serving.

When no verified candidate exists, `context_summary` is JSON `null`; the model
must not generate a narrative about candidate absence. V1-v3 rows remain as
audit history and are excluded from the v4 public response.

### 10.8 Approved v5 structured-narrative architecture (ADR-048)

V5 keeps the existing append-only `ai_reports.content` JSONB storage and does
not require a schema migration. Generation receives a typed evidence bundle and
returns exactly six model-authored fields:

```json
{
  "executive_summary": "...",
  "current_data_interpretation": "...",
  "conditional_scenarios": [{"title": "...", "narrative": "...", "basis": "market_definition"}],
  "factors_to_check": [{"title": "...", "explanation": "...", "basis": "observed_data"}],
  "signals_to_watch": [{"title": "...", "explanation": "...", "basis": "data_limitation"}],
  "evidence_synthesis": null
}
```

`conditional_scenarios` contains one to four distinct conditional items. A
deterministic completeness level restricts the actual count, including exactly
one limitation item when neither a resolution definition nor verified context
exists. Every scenario/check/watch item carries a basis enum tied to available
definition, observed, verified-context, or limitation evidence.
Every authored number must match the supplied metric/market/evidence values;
generic lead text, exact-title mismatch, unsupported procedural detail,
non-conditional scenarios, unavailable basis values, and market/forecast-page
sources fail before storage.

The stored envelope also carries the episode, metric ID, verified candidate
IDs, and ordered evidence references. Deterministic builders add
`relationship_boundary`, `data_limitations`, and `caution_note`. Generation and
read paths independently reconstruct structured evidence and reject any
numeric, temporal, entity, source, or field mismatch.

Quality validation adds issue-specificity, cross-field duplication, Korean
sentence completion, and unsupported-claim checks to the existing strict schema
and wording filters. A failed v5 row is audit-only; the latest valid v5 row
remains public. Older versions remain audit history and cannot satisfy the v5
response contract.

Public source metadata continues to come only from stored verified candidates.
The frontend opens the exact stored URL with safe external-link attributes. A
zero-candidate report is valid but cannot contain `evidence_synthesis` prose or
source links.

### 10.9 Approved v6 mode and reconstruction architecture (ADR-050)

V6 keeps append-only `ai_reports.content` JSONB and requires no migration. A
deterministic selector evaluates the latest linked metric with the existing
`build_expectation_shift_signal()` rule and independently reconstructs zero to
three public verified candidates. Their two booleans select one of four strict
`report_mode` values before the writer is called.

The stored/public envelope adds deterministic `observed_change`,
`resolution_reference`, and `report_mode`, plus a mode-discriminated `briefing`
union. Each narrative block carries one evidence basis from `observed_data`,
`market_definition`, `verified_context`, `general_scenario`, or
`data_limitation`. Only the fields allowed for the chosen mode may be generated
or stored. Fixed no-source/general-scenario labels, metric prose, limitations,
caution, and rule-reference content are rebuilt from stored evidence.

Generation and API reconstruction independently verify the mode, metric,
candidate/source timing, evidence availability, basis enum, allowed fields,
resolution-rule reference, and exact URLs. They also normalize bodies to reject
exact and title-only duplicates, reject high-overlap cross-section prose, and
block authored metric/date/rule repetition. V1-v5 remain audit-only; fallback is
limited to an earlier valid v6 row.

The exact public shape is in
`reports/task-092-evidence-aware-briefing-policy.md`. The user approved the
public API and AI-policy changes on 2026-07-11. Workflow/runtime configuration,
deployment, production writes, new dependencies, and schema changes remain
outside this approval.

### 10.10 Approved v7 writer boundary (ADR-051)

The v7 provider response is limited to `headline`, `summary`, and two-to-eight
flexible sections. Each section has a broad type, title, paragraph-or-bullets
shape, and exact opaque evidence references. Pydantic rejects extra fields,
invalid presentation unions, duplicate references, unknown references, and a
source reference without its parent context reference.

The backend assembles request/report identifiers, observed metrics, context and
source metadata, A-C source levels, supported claims, timestamps, cache state,
data limitations, caution, and last-known-good behavior. Prompt, policy, and
input-schema versions participate in the request fingerprint. Provider output
cannot create or rewrite these fields.

The `v7-positive-evidence-2` policy keeps strict JSON shape, exact evidence
references, source-parent linkage, prohibited-language checks, and authored-URL
blocking. Numeric tokens are no longer a standalone publication blocker;
metrics and definition records remain attributable through section evidence
references, while the prompt asks the writer to copy supplied display values
instead of calculating replacements.

TASK-101 adds only the provider-independent writer boundary. TASK-102 adds the
append-only request/lease schema; TASK-103 adds accepted-source and conditional
verification behavior; TASK-104 connects the asynchronous generation service;
TASK-105 activates the public request/status/cache/report contract.

### 10.11 Approved v8 issue-centered writer boundary (TASK-112)

V8 preserves v7's opaque evidence records, source-parent linkage, A-C source
metadata, append-only requests, cache fingerprinting, last-known-good behavior,
and publication blockers. It changes the writer's organizing structure from
data categories to the reader flow: current situation, recent change,
interpretation, key conditions, what to check next, and an optional single
limitations section.

The writer returns a 10-100 character headline, a 100-500 character two-to-four
sentence summary, and two-to-six uniquely typed sections. `current_situation`
and `recent_change` are required because definition and metric evidence are
always present. References are attached at section level rather than requiring
sentence-by-sentence assembly. V7 prompt/models remain in source for historical
reconstruction. The initial v8 contract used `prompt_version="v8"`,
`policy_version="v8-issue-centered-1"`, and
`input_schema_version="v8-writer-input-1"`; later active policies retain those
rows as last-known-good history.

### 10.12 V8 wider source discovery with narrow excerpt claims (TASK-113)

The on-demand v8 path selects a 90-day horizon for shorter operational issues
and 180 days for longer-horizon or slow-moving policy, diplomatic, legislative,
election, regulatory, treaty, negotiation, and nuclear issues. Deterministic
concept aliases are used both for bounded query construction and for relevance
comparison, so common entity wording differences do not cause an automatic
zero-source result.

Acceptance remains excerpt-bound. A citation title may contribute to topical
relevance, but a non-empty exact annotation excerpt must overlap the issue or
candidate. When the excerpt does not support the candidate's broader condition
wording, the stored excerpt is used as the supported claim. Exact URLs,
publisher identity, A-C attribution, source-parent references, conflict and
high-impact verifier routing, unsafe-domain rejection, and causal/future claim
blockers remain active.

The button-triggered worker now constructs the approved bounded research path
lazily when `refresh_context=true`. A changed evidence bundle creates the
existing immutable successor request, and the request-scoped worker follows
that successor in the same local/development process. Context spend is checked
against the recorded cumulative ceiling before research begins.
Server-tool research does not send Chat Completions JSON mode because the
configured provider rejects web search combined with `response_format`; the
fixed JSON instruction, strict Pydantic parse, annotation provenance checks,
and bounded retry continue to fail closed.
When the tool succeeds with annotations but returns a natural-language body,
the research client does not parse body links or claims. It deterministically
creates one narrow candidate per exact annotation using only title, URL, and
excerpt, then applies the normal relevance and A-D classification path.
The request sets server-tool choice to `required`; a response with zero search
usage and no annotations triggers the one bounded compatibility attempt using
OpenRouter's always-on web plugin. Both paths normalize only `url_citation`
annotations; a second response without annotations still fails closed.

### 10.13 Active-v8 contextual wording validation (TASK-116)

The active writer policy is `v8-contextual-wording-1`. Transactional,
financial-return, participant-following, outcome-endorsement, English, URL,
future-outcome, and unsupported-causality blockers remain deterministic.

Six Korean expressions use an evidence-aware classifier: `확정`, `보장`,
`추천`, `기회`, `전망`, and `원인`. Each authored sentence is checked separately.
Explicit negation/limitation and verification-inquiry patterns pass without a
source. Positive uses require a same-section `source:*` record, a supported
claim containing an approved semantic-strength marker, and visible attribution
in the same sentence. A missing condition fails closed. Generation and
`reconstruct_v8_report()` call the identical validator.

The policy version changes the current request fingerprint. Read-time
reconstruction accepts the historical `v8-issue-centered-1` fingerprint so
previous valid v8 rows remain last-known-good but become stale relative to the
new policy. No schema or public response change is required.

### 10.14 Validated-block writer transport (TASK-117)

The active v8 input schema is `v8-writer-stream-input-1`. The existing
OpenAI-compatible client makes one streaming Chat Completions request without
JSON-object response mode and yields arbitrary text chunks. The worker buffers
those chunks until newline boundaries and accepts only strict NDJSON objects:
one headline/summary block, consecutive uniquely typed sections, and a final
count object.

Each complete authored block passes exact Pydantic shape validation, evidence
and source-parent checks, URL and wording filters, and accumulated section
order/uniqueness checks before an append-only block row commits. The final
object constructs the normal `V8WriterOutput` and reruns the complete validator
before the unchanged `ai_reports` success row and request outcome are stored.
Provider usage plus first-validated-block and total-writer milliseconds are
recorded on the terminal request event. A non-streaming client is retained only
as a compatibility path and publishes blocks after the full output validates.

---
