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
5. Store the signal independently. Normal collection does not invoke briefing generation; a later user request fingerprints the latest eligible evidence.

---

## 9. Active Collection and Briefing Architecture

Market collection and briefing generation are separate runtime paths.

```text
four-hour workflow
  Gamma fetch -> normalize -> snapshots -> metrics -> signals -> collection log
  (no provider client, no context research, no briefing writer)

user request
  current evidence -> immutable fingerprint/request -> isolated worker
  -> optional bounded context refresh -> one v8 NDJSON response
  -> validate/persist complete blocks -> validate/store final report
  -> append request outcome -> SSE replay or polling
```

The API process may append or join a generation request after the current
evidence bundle is available. It does not call Polymarket or a provider. The
worker owns provider access, validation, report persistence, and terminal
request events.

Duplicate requests for the same market/fingerprint join one immutable identity.
A worker uses a bounded lease for running attempts. Provider, parse, evidence,
source, wording, or persistence failure keeps the previous valid report.

## 10. Active V8 Writer and Output Design

### 10.1 Evidence bundle

The frozen input contains the market definition revision, metric and eligible
snapshot, observed-history summary, caution inputs, accepted context/sources/
claims, timestamps, limitations, and opaque evidence references. Prompt,
policy, and input-schema versions participate in the fingerprint.

### 10.2 Writer output

One request emits strict NDJSON: one headline/summary object, two-to-six
consecutive section objects, then one complete object. Required section types
are `current_situation` and `recent_change`; optional types are
`interpretation`, `key_conditions`, `what_to_watch`, and `limitations`.

A paragraph has content only; a bullet section has items only. Every section
has one or more exact evidence references. The writer cannot create source
records, identifiers, metrics, dates, cache state, limitations, caution, or
URLs.

### 10.3 Validation and storage

Each complete block passes strict shape, order, uniqueness, evidence,
source-parent, URL, future/relationship, and active wording checks before its
append-only row commits. The complete object rebuilds the normal v8 output and
runs the full validator before `ai_reports` and the success event commit.

Read-time reconstruction independently repeats generation-time metric,
snapshot, definition, context, source, claim, fingerprint, timing, caution, and
wording checks. An invalid newest row is skipped in favor of an earlier valid
v8 row.

### 10.4 Historical contracts

V1-v7 prompts, shapes, and generation modes are no longer active product
contracts. Accepted decisions remain in `memory/decisions.md`, and detailed
artifacts remain recoverable from Git history.

### 10.5 V8 issue-centered writer boundary

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

### 10.6 V8 wider source discovery with narrow excerpt claims

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

### 10.7 Active-v8 contextual wording validation

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

### 10.8 Validated-block writer transport

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

### 10.9 Tool-free scenario boundary

The next-contract scenario path is separate from active v8 and has no agent
loop. One authenticated user turn appends one immutable request; one isolated
worker makes at most one provider call. The model receives a typed, read-only
bundle containing the selected issue definition, exact observations, accepted
sanitized source excerpts, server-owned premise classes, bounded prior turns,
and the latest untrusted user message.

The model has no database, browser, URL fetch, code execution, external action,
or second-call capability. It cannot change a premise class. The initial
release permits at most eight user turns and does not use model-authored
conversation compaction.

Free-form presentation uses a minimal internal envelope with authored Markdown,
referenced premise IDs, and optional generic new scenario premises. The server
forces new premises to `model_scenario`, adds timing/policy/caution metadata,
and validates complete paragraph/list blocks before storage and authenticated
fetch-SSE replay. Raw provider chunks, links, HTML, images, forms, and embedded
content never become public blocks.

The request-scoped worker claims one queued request, builds the typed bundle,
performs one non-tool provider call, and stores only a completely validated
assistant turn, model-scenario premises, blocks, and terminal usage event.
Expiry or owner deletion prevents later persistence and removes the ephemeral
conversation graph. Earlier v8 reports and all issue/evidence history remain
untouched. Migration 006 is required wherever the scenario API is enabled.

---
