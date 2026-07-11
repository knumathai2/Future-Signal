<!--
Purpose:        Key technical decision history in ADR format
Owner:          PM / Backend Implementer
Update Trigger: Record immediately after any significant technical or scope decision
Harness Version: 1.1
-->

# Decision Log — Outlook Signals

_Last updated: 2026-07-11_

## Template

```
### ADR-NNN: [Decision Title]
- **Date**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Decided by**: [Role / User]

**Context**: Why was this decision needed?
**Decision**: What was chosen?
**Rationale**: Why was this chosen?
**Trade-offs**: What are the downsides?
**Consequences**: What changed as a result?
```

---

### ADR-048: Expand v4's two authored fields into evidence-bounded narrative summaries

- **Date**: 2026-07-11
- **Status**: Accepted ⚠️ HUMAN APPROVAL
- **Decided by**: User (human), PM / Planner

**Context**: The user inspected an actual TASK-065 development-DB v4 report in
the local UI. Although generation and display worked, only `issue_overview` and
`what_to_check` were model-authored. The result was generic, awkward, and hard
to distinguish from deterministic template copy. Verified source links were
already supported conditionally, but no candidate passed the development
backfill gates, so no real source card was visible.

**Decision**: Approve TASK-075~081 to introduce a richer v5 structured narrative
report, improve verified article/official-document retrieval, expose exact
stored source links, regenerate representative development reports, and place
the real results in front of the user for a final quality decision. The model
may choose prose and organization within six named narrative fields, but every
fact, number, date, named entity, and source claim must resolve to supplied
metric/market/verified-candidate evidence. Deterministic relationship,
limitation, and caution fields remain mandatory. Generic, duplicated,
incomplete, unsupported, causal, outcome-asserting, or prohibited-language
output is rejected before storage.

**Rationale**: Perceived AI value comes from useful evidence transformation,
not from an AI label. Wider prose freedom can improve readability and
specificity without relaxing the product's epistemic or publication boundary.
Direct verified-source links let users inspect the material behind a summary.

**Trade-offs**: Longer output costs more, has more failure modes, and requires
new quality gates plus a public API/UI version change. When no candidate passes
verification, the report must remain a metric-grounded summary and cannot
claim external context depth.

**Consequences**: ADR-003's blanket phrase "never free-form analysis" is
superseded only by this evidence-bounded structured-narrative contract. The
prohibition on unconstrained or evidence-free analysis remains. TASK-075~081
may change the report policy and approved public API/UI shape and may write new
reports/context audit rows only to local/development databases within the
existing cumulative USD 100 program ceiling. Deployment, production writes,
infrastructure changes, new dependencies, unrelated schema/API changes, and
existing-migration edits remain outside approval.

**2026-07-11 user-format amendment**: The user supplied three target examples
covering geopolitical, monetary-policy, and legislation issues. V5 adopts their
shared reading order: executive summary, current-data interpretation, three to
four conditional scenarios, factors to check, observable follow-up materials,
verified sources, and caution. Wording that implies a cause, assigns unsupported
future likelihood, or suggests an action is rewritten as conditional observation
without reducing the desired depth. The exact reference contract is recorded in
`reports/task-077-ai-summary-reference-format.md`.

---

### ADR-050: Select v6 briefing structure from change and verified-evidence state

- **Date**: 2026-07-11
- **Status**: Accepted ⚠️ HUMAN APPROVAL
- **Decided by**: User (human), PM / Planner

**Context**: The current v5 report can repeat the same metric and market
resolution content in its summary, current-data interpretation, scenarios, and
check cards. When verified public material is absent, its fixed six-field shape
also creates large low-information sections instead of adapting to the actual
evidence level.

**Decision**: Select one of four v6 modes from two deterministic facts: whether
the latest linked metric meets the existing 24-hour ±5pp
`expectation_shift` rule, and whether at least one same-episode candidate passes
the strict verified-source read contract. Each mode has an exact authored-field
allowlist and typed evidence bases. General scenarios are permitted only as
clearly labelled non-current explanations; they cannot add unsupported recent
facts, person states, concrete procedures, causal assertions, likelihood ranks,
outcome assertions, or action prompts. Current metric data and resolution rules
are deterministic and each has one display owner; rules move to a collapsed
`판정 기준 보기` reference region.

**Rationale**: Information structure should follow available evidence rather
than requiring every issue to fill the same cards. Reusing the existing signal
threshold and verified-candidate gates keeps mode selection reproducible and
prevents the model from deciding how strong its own evidence is.

**Trade-offs**: V6 replaces the current public report shape, adds a new evidence
basis, and requires discriminated Backend/Frontend validation. Strict duplicate
and rule-leak checks will reject some otherwise readable generations. General
scenario copy remains intentionally limited when no attributable source exists.

**Approval boundary**: The product behavior and proposed exact contract are in
`reports/task-092-evidence-aware-briefing-policy.md`. No schema change or new
dependency is proposed. TASK-093 and TASK-095 runtime implementation require
explicit approval of (1) the bounded general-scenario AI-policy change and (2)
the v5-to-v6 public report API change. Workflow/runtime configuration changes,
deployment, production writes, existing-migration edits, and wording-policy
changes remain separate gates.

**Approval follow-up (2026-07-11)**: The user explicitly approved both the
bounded general-scenario AI-policy change and the exact v5-to-v6 public report
API contract. TASK-093 and TASK-095 may implement those approved scopes in
dependency order. This approval does not include workflow/runtime
configuration, deployment, production writes, schema changes, new dependencies,
existing-migration edits, or wording-policy changes.

**Consequences**: TASK-092 is complete and TASK-093 is active. TASK-094~098
remain dependency-gated in `tasks/active.md`.

---

### ADR-001: AI Development Harness v1.1 Adoption

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User

**Context**: A 4-person, 5-day hackathon team needs consistent context handoff between people/sessions and a shared scope-control mechanism.
**Decision**: Adopt AI Development Harness v1.1 (Standard tier) to structure agent roles, workflows, and memory.
**Rationale**: Eliminates context loss between sessions; gives the PM a concrete scope-gate mechanism (roadmap.md P0/P1/P2 tables) against the "trying to build everything at once" risk already flagged in PRD §15.1.
**Trade-offs**: Upfront documentation overhead on Day 1, when time is scarcest.
**Consequences**: All 4 roles operate from a shared, consistent context; PM enforces scope via `roadmap.md` and `AGENTS.md`.

---

### ADR-002: MVP scope narrowed to "sudden-change issue monitoring" (from broader "global issue outlook platform")

- **Date**: 2026-07-07 (recorded in PRD v1.1)
- **Status**: Accepted
- **Decided by**: PM / User

**Context**: The earlier PRD concept was too broad for 5 days / 4 people.
**Decision**: Fix the core experience to "check today's most-changed issues → detail chart → template summary + caution notice"; limit to 30–50 binary markets; template-based AI only; 3–5 manually-curated related events; exclude saving/notifications/reports/sharing/chart-export.
**Rationale**: A narrow, fully-working demo beats a broad, half-working one for hackathon judging (PRD §1.4, §15.5).
**Trade-offs**: Cuts real product features (personalization, saved issues, weekly reports) that have genuine user value — deferred to Phase 2/3.
**Consequences**: PRD §6.3–6.5 P0/P1/P2 tables are the binding scope contract; any request to add P2 features requires HUMAN APPROVAL per `AGENTS.md`.

---

### ADR-003: Template-constrained AI output only, never free-form analysis

- **Date**: 2026-07-07 (Service Design §6, Technical Design §10)
- **Status**: Accepted
- **Decided by**: PM / Data-AI Implementer

**Context**: Free-form LLM analysis on financial/prediction-market data carries high risk of causal assertions, overstated confidence, or advice-like language.
**Decision**: LLM is used only to fill fixed template slots (issue_summary, movement_explanation, key_change_context, uncertainty_summary, neutral_conclusion); every output passes a banned-phrase filter before storage; failed generations discard and keep the previous report live rather than auto-retrying.
**Rationale**: Keeps token cost predictable, keeps legal/ethical exposure low, matches the product's "not a prediction service" positioning (PRD §15.3, §15.4).
**Trade-offs**: Less rich/flexible output than a free-form analyst LLM would produce.
**Consequences**: All future AI output types must pass through the same filter before ship (Service Design §6, standing rule).

---

### ADR-028: AI report output shifts from metric summary to issue explainer scenarios

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User / Data-AI Implementer

**Context**: The first stored AI summaries were too numeric for general readers: they repeated current value and movement figures but did not clearly explain what the issue means or how to read the market question. The user approved changing the public `/api/issues/{id}/report` content shape.
**Decision**: Replace the old 5-slot report content (`issue_summary`, `movement_explanation`, `key_change_context`, `uncertainty_summary`, `neutral_conclusion`) with 8 fixed slots: `issue_explainer`, `why_it_matters`, `current_reading`, `scenario_major_change`, `scenario_limited_change`, `scenario_status_quo`, `check_points`, and `caution_note`.
**Rationale**: The new structure helps non-specialist users understand the issue itself, why it matters, what the current data reading suggests in neutral language, and three conditional paths without using value-loaded "best/worst" labels or predicting an outcome.
**Trade-offs**: This is a public API shape change and old successful `ai_reports` rows no longer validate against the current response schema. They are treated as `not_yet_generated` until a v2 report is generated.
**Consequences**: `PROMPT_VERSION` advances to `v2`; backend/frontend report schemas and rendering are updated; the database schema remains unchanged because `ai_reports.content` is `jsonb`; all generated content still must pass the banned-phrase/pattern safety filter before storage.

---

### ADR-029: Dashboard uses Korean issue display copy instead of raw market titles

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User / Frontend Implementer

**Context**: The dashboard's raw Polymarket titles were English question strings, making it hard to understand the issue at a glance.
**Decision**: Keep the API and stored source title unchanged, but map frontend issue cards/detail headers to Korean display copy: topic label, short issue title, one-line 기준 조건, and a detail-only original market question.
**Rationale**: This improves scanability without adding a schema migration or changing the public API. The original title remains available for provenance on the detail screen.
**Trade-offs**: The first pass uses deterministic frontend mappings for the current live/demo issue set plus conservative fallbacks. New unseen market titles may need additional mapping polish later.
**Consequences**: Main dashboard cards show Korean issue names first; English source titles are no longer the primary card headline.

---

### ADR-030: Live categories and current-version report rows drive demo reads

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User / Debugger

**Context**: After `TASK-043`, the configured development DB still had legacy
v1 report rows and no v2 rows, so the detail report card showed the accepted
`not_yet_generated` state. After v2 rows were generated, v1/v2 rows could share
the same metric timestamp, making `generated_at DESC` alone unstable. The
dashboard category buttons also came from a fixed sample list while live DB
categories used source tag labels such as `Politics` and `Crypto`.
**Decision**: `/api/issues/{id}/report` now requests only the current
`PROMPT_VERSION` row from the report read helper. Legacy prompt-version rows
remain stored for traceability and regeneration eligibility but are not served.
The report batch also prefers current-version rows when deciding whether an
issue already has a fresh report. `/api/categories` now derives categories from
currently servable live issues when DB data exists, while `/api/issues`
category filtering is case-insensitive.
**Rationale**: This keeps the v2 issue-explainer UI deterministic, avoids
serving old report shapes, prevents repeated generation for rows that already
have current-version reports, and makes filter buttons point at categories that
can actually return issues.
**Trade-offs**: Categories now reflect raw stored source labels rather than a
manually curated taxonomy. A later taxonomy task can group labels into broader
Korean categories if needed.
**Consequences**: The configured development DB was regenerated through the
guarded reports-only path and now has v2 stored summaries for the default
top-20 heat-sorted issues. No schema, dependency, deployment, infrastructure,
or public response-shape change was made.

---

### ADR-031: Category filters use broad Korean taxonomy

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User / Debugger

**Context**: Live source categories such as `Politics`, `Crypto`, and
`Ukraine` were technically accurate but not scan-friendly for a Korean demo.
The user first requested Korean category labels and recognizable conflict
groups, then clarified that the top filter should remain broad like `정치` and
`경제` while card-level labels should stay detailed.
**Decision**: Add a backend taxonomy that derives broad Korean filter labels
from each issue's stored category and title. `/api/categories` returns broad
labels such as `정치`, `경제`, `환경`, `기술`, `세계`, and `스포츠` when
matching issues are servable. `/api/issues?category=...` accepts those Korean
labels while still accepting raw stored category values for backward
compatibility. More specific labels such as `우크라이나 전쟁` and `이란 전쟁`
remain frontend card-display labels, not top-level filter buttons.
**Rationale**: The filter buttons stay simple and scan-friendly while the cards
still communicate recognizable topics at a glance. This also avoids a schema
migration or public issue response shape change.
**Trade-offs**: This is a deterministic heuristic taxonomy, not a full
editorial classification workflow. Specific conflict labels are no longer
top-level filters, so users browse them through the broader `세계` category and
the card label.
**Consequences**: Category buttons are broad Korean groups on the live
dashboard; cards keep detailed topic labels via the frontend display layer.
Synthetic tests cover Ukraine/Iran-style conflict issues mapping to `세계`.

---

### ADR-032: v3 AI Report Policy and Scope Lock

- **Date**: 2026-07-10
- **Status**: Accepted
- **Decided by**: User / PM Planner

**Context**: v2 reports are live as fixed issue explainers, but v3 implementation
would touch the public `/api/issues/{id}/report` response, AI prompt/schema
contract, frontend report rendering, and copy policy. This approval must land
before Frontend, Backend, or Data/AI implementation begins, because
`AGENTS.md` gates public API shape changes and wording-policy changes behind
human approval. PRD and Service Design still prohibit free-form analysis,
future-outcome claims, causal news matching, action-oriented wording, and
wallet/participant-level surfaces.

**Decision**: Approve v3 as a scope-locked, template-constrained report update.
The only approved public API change is the v3 report response shape listed
below. No database schema migration, new endpoint, infrastructure change,
deployment, paid external API call, or production/shared database write is
approved by this ADR. v3 implementation tasks may begin only after this ADR is
read as their prerequisite and must stay within the field list and policy below.

**v3 AI summary/report policy**:

- v3 remains a fixed-schema data summary/report, not open-ended analysis.
- The model may only fill named slots from structured inputs that the pipeline
  already computed or PM/Data manually curated.
- The report may describe observed movement, current data reading, conditional
  scenario context, check points, and interpretation limits.
- The report must not assert causes, predict outcomes, rank actions, or imply
  that the data represents the public at large.
- Every successful report must include a caution section and must carry a
  data-as-of timestamp through the API response.
- A safety failure blocks storage and keeps the previous successful current
  report live. Do not auto-retry a safety-filter failure with the same prompt.
- Legacy v1/v2 report rows remain audit history. They must not be served as v3
  content unless they validate against the v3 schema and current prompt version.

**Approved public API shape changes**:

- `GET /api/issues/{id}/report` may add `report_version` to successful
  responses, derived from the current prompt/schema version.
- Successful `content` becomes exactly the fixed v3 field set below.
- `context_candidate_note` is the only nullable content field. If it is `null`,
  the frontend hides that section.
- `status="not_yet_generated"` and unknown-id `404` behavior stay unchanged.
- No new report-generation endpoint, user-facing regenerate button, issue-list
  field, history field, category field, or signal field is approved here.
- No schema migration is approved. The existing `ai_reports.content` JSONB
  storage may hold the v3 object, and `prompt_version` remains the storage-side
  compatibility gate.

**Final v3 field list**:

| Field | Type | Nullable | Producer / owner | Exposed through API | UI usage | Safety/copy validation required |
|---|---|---:|---|---|---|---|
| `id` | UUID string | No for success; absent for `not_yet_generated` | Backend | Yes | Report identity / React key only | No |
| `status` | enum: `success`, `not_yet_generated` | No | Backend | Yes | Report state rendering | No |
| `report_version` | string, expected `v3` for this policy | No for success | Backend from `prompt_version` | Yes | Optional debug/support display; not a marketing label | No |
| `generated_at` | ISO 8601 timestamp | No for success | Data/AI batch | Yes | Report freshness | No |
| `data_as_of` | ISO 8601 timestamp | No for success | Backend from `input_metrics_id` -> `market_metrics.computed_at` | Yes | Required timestamp near report | No |
| `prompt_version` | string | No | Data/AI batch | No | Storage/read compatibility gate | No |
| `model_used` | string | Yes | Data/AI batch | No | Internal audit only | No |
| `input_metrics_id` | bigint | No for generated rows | Data/AI batch | No | Traceability to computed metrics | No |
| `content.issue_explainer` | string | No | Data/AI template | Yes | "Issue summary" section | Yes |
| `content.why_it_matters` | string | No | Data/AI template | Yes | "Why it matters" section | Yes |
| `content.current_reading` | string | No | Data/AI template | Yes | Current data reading section | Yes |
| `content.recent_change_summary` | string | No | Data/AI template from computed metrics | Yes | Recent movement section; includes window, direction, magnitude, and observed timing when available | Yes |
| `content.context_candidate_note` | string | Yes | PM/Data manual related-event candidate, phrased by Data/AI template | Yes | Optional manually curated context candidate section | Yes |
| `content.scenario_major_change` | string | No | Data/AI template | Yes | Conditional scenario section | Yes |
| `content.scenario_limited_change` | string | No | Data/AI template | Yes | Conditional scenario section | Yes |
| `content.scenario_status_quo` | string | No | Data/AI template | Yes | Conditional scenario section | Yes |
| `content.check_points` | string | No | Data/AI template | Yes | Verification/check-points section | Yes |
| `content.caution_note` | string | No | Data/AI template | Yes | Required caution note | Yes |
| `content.data_limitations` | string | No | Data/AI template from confidence/caution inputs | Yes | Data limitations section; activity, volatility, history, and source limitation language | Yes |

**Approved wording/safety policy changes**:

- v3 tightens the existing policy; it does not remove any prohibited term.
- English hard-block terms remain the `standards.md` and `memory/glossary.md`
  list: `bet`, `buy`, `sell`, `trade`, `position`, `long`, `short`, `profit`,
  `win rate`, `odds`, `copy trader`, `follow this user`, `expert trader`,
  `best pick`, `recommended outcome`, `high-return opportunity`, `guaranteed`,
  `guaranteed prediction`, `signal to act`, `recommend`, and `recommendation`.
- Korean UI/template output must also avoid direct action, return, certainty,
  and copy-participant wording, including: `베팅`, `매수`, `매도`, `포지션`,
  `롱`, `숏`, `수익`, `승률`, `배당`, `추천`, `보장`, `확정`, `따라하기`,
  `고수`, `전문 트레이더`, `고수익`, and `기회`.
- Approved replacement language: "reflected expectation value",
  "observed movement in public data", "interpretation-caution badge",
  "related event candidate", "context candidate that can be checked alongside
  the change", "data reliability", "public data reading", and Korean
  equivalents such as `공개 데이터에 반영된 기대값`, `관찰된 변화`,
  `해석 주의`, `맥락 후보`, and `공개 데이터 읽기`.
- Ambiguous wording rules:
  - `signal` may appear only as a neutral compound label such as
    `Expectation Shift Detected`; never as a standalone action cue.
  - `confidence` must mean data reliability, not outcome certainty.
  - `likely`, `will`, `must`, and Korean future/certainty equivalents must not
    describe real-world outcome probability.
  - Causal connectors are prohibited in generated/user-facing output when
    linking context to movement. Use timing/co-occurrence phrasing only.
  - A related/context candidate must carry a candidate-not-cause qualifier in
    the same sentence or adjacent UI text.
- Validation before AI output is stored:
  - Parse exactly the v3 schema, reject missing or extra fields.
  - Run the English and Korean hard-block term scan with case folding.
  - Run pattern checks for action advice, future-outcome claims, causal claims,
    participant-following language, and certainty framing.
  - Require non-empty `caution_note` and non-empty `data_limitations`.
  - Before storing a success row, require `input_metrics_id` to resolve to a
    `market_metrics.computed_at` timestamp. The API derives top-level
    `data_as_of` from that relationship when reading the report; `data_as_of`
    is not added to `ai_reports.content` and does not require a schema change.
  - If `context_candidate_note` is non-null, require candidate-not-cause
    language before storage.
  - On any failure, discard the generated content, log the failure reason, and
    keep the previous successful current-version report as the served response.
- Shared standard: the same criteria apply to UI copy, AI templates, fallback
  strings, demo-visible docs, and generated report content. Policy/lint docs
  and tests may quote prohibited expressions only to define or verify blocks.

**Allowed vs prohibited automated news matching scope**:

| Scope | Decision |
|---|---|
| Manually curated related-event candidates for 3-5 demo issues | Allowed and remains the MVP path. PM/Data must approve the candidate text before it is seeded or displayed. |
| Non-public candidate-discovery helper | Allowed only as an offline PM review aid if it does not call paid APIs without approval, does not write to the DB, does not change the public API, and does not display results to users. |
| Automated candidate scoring, ranking, or confidence labels | Prohibited for MVP/v3. |
| Scheduled news crawler or background matcher | Prohibited for MVP/v3. |
| Automatically writing `related_events` rows from news/search output | Prohibited for MVP/v3. |
| Displaying algorithmically matched news as related to an issue | Prohibited for MVP/v3 unless a future ADR and human approval redefine the scope. |
| Any phrasing that states or implies the event caused the data movement | Prohibited. |

**Maintained prohibitions**:

- No free-form/open-ended AI analysis.
- No causal claims, future-outcome predictions, or action-oriented language.
- No automated public news-to-market matching in the product.
- No wallet-level, participant-level, leaderboard, following, or copy-style
  feature.
- No accounts, saving/watchlist, notifications, weekly reports, team sharing,
  chart export, or other P1/P2 feature pulled into MVP by this ADR.
- No data-bearing screen without data-as-of timing and interpretation caution.
- No new dependency, schema change, infrastructure/deployment change, paid
  external API call, shared/prod database write, or existing migration edit.

**Rationale**: v3 improves report clarity by separating recent movement,
manual context candidate, and data-limit sections while preserving the
template-first safety model. The field list is small enough for Day 5 follow-up
implementation and explicit enough for Backend, Frontend, and Data/AI to work
without re-opening policy scope.

**Trade-offs**: v3 adds a public response-shape change and requires coordinated
Backend, Frontend, and Data/AI updates. It also keeps automated news matching
out of the public product, so context coverage remains narrower than a fully
automated news system.

**Consequences**:

- `TASK-047` completes the prerequisite approval gate for v3 implementation.
- Frontend, Backend, and Data/AI implementers may start v3 implementation only
  from this ADR and must not expand beyond the approved field list.
- `backend/API_CONTRACT.md`, backend schemas/tests, report prompt/schema,
  frontend report rendering, fallback report sample, and copy lint rules need
  coordinated follow-up updates.
- Current v2 rows remain valid historical rows, but v3 UI/API work must serve
  only current-version v3-compatible successful report rows.

**Follow-up tasks and dependencies**:

| Follow-up | Owner | Dependency | Scope boundary |
|---|---|---|---|
| Data/AI v3 prompt/schema/safety-filter update | Data/AI Implementer | ADR-032 | Implement only the fields and validation rules above; no free-form prompt expansion. |
| Report API contract/schema update | Backend Implementer | ADR-032 and Data/AI schema constants | Expose only `report_version` plus the approved v3 `content` fields; no new endpoint or migration. |
| Report UI rendering update | Frontend Implementer | Backend contract update or matching mock JSON | Render/hide only approved v3 fields and keep caution/data-as-of visible. |
| Copy/safety lint pass | PM / Reviewer | Frontend/Data/AI changes complete | Must pass before demo or merge; policy-list hits are allowed only in lint docs/tests. |
| Optional offline candidate-discovery helper | PM/Data only | Separate task and approval if paid API or DB write is involved | Non-public review aid only; cannot auto-seed or display matches. |

---

### ADR-033: Eight-field v3 Report Contract supersedes ADR-032

- **Date**: 2026-07-10
- **Status**: Accepted
- **Decided by**: User / PM, drafted by Backend Implementer
- **Supersedes**: ADR-032 for the v3 report content and display contract only

**Context**: ADR-032 approved an eleven-field v3 report shape. TASK-048 was
assigned to evaluate a different eight-field `ReportContent` contract and to
produce a complete Backend decision table, Data/AI safety review, and Frontend
display review before any runtime change. The accepted TASK-048 contract
differs from ADR-032, so the replacement must be recorded without rewriting
ADR-032's history.

**Decision**: Accept the TASK-048 contract in `backend/API_CONTRACT.md` as the
frozen v3 implementation contract. Successful v3 `content` contains exactly:

1. `issue_overview`
2. `current_data_reading`
3. `possible_outlook`
4. `possible_drivers`
5. `external_context`
6. `what_to_check`
7. `data_limitations`
8. `caution_note`

`external_context` is the only nullable value; its key remains required and the
Frontend hides its complete section only when the value is `null`. Narrative
context comes only from the PM/Data-approved curated path. Existing
issue-detail `related_events` remains the source-metadata area; source URL and
stored review-status metadata are not added.

The approved trimmed Unicode-code-point length bounds are:

| Field | Minimum | Maximum |
|---|---:|---:|
| `issue_overview` | 30 | 600 |
| `current_data_reading` | 50 | 700 |
| `possible_outlook` | 60 | 700 |
| `possible_drivers` | 80 | 700 |
| `external_context` when non-null | 40 | 700 |
| `what_to_check` | 30 | 600 |
| `data_limitations` | 80 | 700 |
| `caution_note` | 120 | 700 |

Each generated narrative field is limited to 1-5 concise sentences. Backend
and Frontend must use the same trimmed Unicode-code-point measurement if both
validate content.

Retain `possible_outlook` only for conditional descriptions of later public
data readings, never a real-world result or asserted future direction. Retain
`possible_drivers` only as a deterministic index of manually reviewed context
candidate title/date with an explicit no-relationship statement. The approved
Frontend labels are `Conditional Developments` and `Factors to Check Alongside
the Movement`, with the Korean labels and evidence-first order frozen in the
API contract.

Use external-context Option A, the exact provenance boundary, current caution
enum semantics and precedence, deterministic Korean caution literals, and the
approved missing-value behavior in `backend/API_CONTRACT.md`. Top-level
`confidence_level` is not added; the stored report's required `caution_note`
is the report-snapshot caution indicator. Successful responses still require
`report_version="v3"`, `generated_at`, `data_as_of`, and `status="success"`.
The accepted `not_yet_generated` and unknown-ID behavior remain unchanged.

**Safety boundary**: ADR-033 keeps every maintained prohibition and validation
rule from ADR-032 unless this decision explicitly replaces a content-field or
display detail. Output remains fixed-schema and template-constrained. No causal
claim, real-world outcome assertion, action-oriented wording, automated public
context matching, or unreviewed external context is allowed.

**Rationale**: The eight-field contract gives each report section one clear
responsibility, separates reviewed context narrative from candidate comparison,
keeps data limitations and interpretation caution explicit, and provides a
single enforceable contract for Backend, Data/AI, and Frontend implementation.

**Consequences**:

- ADR-032 remains immutable historical context but no longer defines the v3
  content/display contract; ADR-033 is the implementation prerequisite.
- TASK-048 is complete as contract design and approval work.
- Runtime Backend, Data/AI, and Frontend remain on v2 until separate coordinated
  implementation tasks switch schema, generation, tests, types, and UI
  together.
- No database migration, new endpoint, dependency, infrastructure change,
  deployment, external provider call, or database write is approved or
  performed by this decision.

---

### ADR-034: TASK-049 splits v3 content into LLM-authored prose and deterministic template fields

- **Date**: 2026-07-10
- **Status**: Accepted (implementation-scope note, not a policy/field-list/schema
  change - no human approval gate applies)
- **Decided by**: Data/AI Implementer

**Context**: ADR-033 requires an exact deterministic Korean `caution_note`
literal per `confidence_level`, a `possible_drivers` value that is "a
deterministic index" and never a causal explanation, and an `external_context`
that is a verbatim pass-through of a PM/Data-reviewed note with "no new
inference ... added." Asking an LLM to reproduce those fields freely each call
would risk inexact caution copy, invented candidate detail, or paraphrased
provenance - all of which ADR-033 treats as validation failures.
**Decision**: `app/core/ai_report.py`'s v3 prompt asks the model for exactly
three fields - `issue_overview`, `current_data_reading`, `possible_outlook`.
`possible_drivers`, `external_context`, `what_to_check`, `data_limitations`,
and `caution_note` are built deterministically in code from
`ReportPromptInputs` (stored/curated values only) and merged with the LLM's
three fields by `assemble_report_content()` into the frozen eight-field
`ReportContent`. The related-event candidate (title/date/note) is never
inserted into the LLM prompt at all, so the model cannot weave it into
`possible_outlook`/`current_data_reading` with causal framing. `caution_note`
is selected from an exact-literal lookup table keyed by `confidence_level`;
`data_limitations` independently checks missing-history/low-activity/
high-volatility flags from raw snapshot/metric inputs (not the collapsed enum
alone) so one enum value can't hide another real limitation.
**Rationale**: Keeps the legally/ethically sensitive fields under full
program control instead of LLM sampling variance, exactly matching ADR-033's
"deterministic template" and "exact deterministic Korean template" language
for these fields, and makes the DoD's deterministic-caution and
no-candidate/weak-inference test requirements exactly assertable.
**Trade-offs**: `possible_drivers`/`what_to_check` read as more formulaic than
free LLM prose. `ReportPromptInputs` grew new fields (`outcome_label`,
`end_date`, `volume_24h`, `liquidity`, `related_event_title`,
`related_event_date`, `related_event_note`) that `app/core/ai_report_batch.py`
now populates from `Market`/`MarketSnapshot`/`MarketOutcome`/`RelatedEvent`
rows already in scope for TASK-049 (Data/AI owns `ai_report_batch.py`).
**Consequences**: `app/core/ai_report.py` defines its own local `ReportContent`/
`LLMReportFields` Pydantic models (a structural copy of the ADR-033 contract),
kept separate from `app/schemas/issues.py` so this task and Backend's
TASK-050 (which owns the public API/Pydantic schema) do not collide on the
same file - matching `reports/day-5-v3-implementation-allocation.md`'s
parallelization plan. `PROMPT_VERSION` is now `"v3"`. `parse_report_content`
is replaced by `parse_llm_fields` (validates only the three LLM fields) plus
`assemble_report_content` (merges and validates the full eight-field object);
`run_semantic_checks` adds cross-field checks (exact caution literal,
exact possible_drivers literal, external_context candidate-not-cause
qualifier) beyond the existing banned-phrase/pattern filter, which itself
gained the ADR-033 Korean hard-block terms and Korean causal/forecast
patterns (with a carve-out so the approved "예측시장" - prediction market -
domain term is never mistakenly flagged by the new forecast-word ban). No
live provider call or configured/shared database write was made implementing
or testing this - all tests run against a fake `LLMClient` and in-memory
SQLite.

---

### ADR-035: Scheduled batch uses complete repository configuration and explicit v3 prompt constraints

- **Date**: 2026-07-10
- **Status**: Accepted (human-approved configuration repair; no product-policy,
  schema, dependency, or public API change)
- **Decided by**: User request, implementing Debugger / Data-AI Implementer

**Context**: The first scheduled GitHub Actions run failed because the
repository had no Actions secrets, leaving `DATABASE_URL` and the AI credential
empty. After restoring them, the workflow fallback model produced valid JSON
whose prose often missed ADR-033's already-approved character bounds or the
existing public-participant-data and conditional-later-data checks. The
repository `OPENAI_MODEL` variable was also absent, so Actions did not use the
approved project model configured for local development.
**Decision**: Store the approved development `DATABASE_URL` and AI credential
as repository Actions secrets without printing their values; set the
`OPENAI_MODEL` repository variable to the approved project model; and repeat
ADR-033's existing Unicode bounds, exact Korean public-data source compound,
and current-reading scope directly in the fixed three-field LLM prompt. Keep
all structural, wording-safety, and semantic filters unchanged.
**Rationale**: A scheduled environment must receive the same approved project
configuration as the guarded local path, and the model prompt should state the
same constraints that the mandatory pre-storage validators enforce. This fixes
runtime drift without weakening the policy or accepting invalid prose.
**Consequences**: GitHub Actions branch run `29073226485` completed with 50
processed rows, 0 collection failures, and 10 successful reports. Read-only
post-run validation confirmed the latest 10 v3 rows pass the structural,
wording-safety, and semantic checks. Draft PR #51 carries the prompt/test
changes; `main` requires the normal review flow before those code changes land.
The runner's separate Node.js action-runtime deprecation warning is tracked as
TD-012.

---

### ADR-036: Browser routes separate discovery, exploration, detail, and methodology

- **Date**: 2026-07-10
- **Status**: Accepted
- **Decided by**: User / Frontend Implementer

**Context**: The dashboard rendered the full issue set, a repeated weekly list,
filters, and detail/notice state in one React-state flow. Detail and notice
screens therefore remained at `/`, could not be shared or refreshed directly,
and made the mobile discovery screen excessively long.
**Decision**: Add the user-approved `react-router-dom@^7.18.0` dependency and
split the browser surface into `/`, `/issues`, `/issues/:issueId`, and
`/methodology`, with a client-side 404. Home shows one featured issue, four
unique compact rows, and category summaries. `/issues` owns URL-backed search,
category, 24-hour/7-day window, sorting, and 10-row numbered pagination. Detail
core data, 30-day history, and the stored report load independently with request
cancellation. Add scoped Vercel rewrites for `/issues`, `/issues/:path*`, and
`/methodology` only, with the Vercel project root remaining `frontend/`.
Use the approved short caution copy: “공개 데이터에 반영된 기대값의 변화이며,
전체 대중의 판단을 대표하지 않아 해석에 주의가 필요합니다.”
**Rationale**: This implements the existing Home → Issue List → Detail product
flow, makes list/detail URLs shareable, answers the discovery question earlier,
and preserves the read-only backend contract.
**Trade-offs**: The frontend now owns client-side query normalization and
pagination over up to 100 summary rows. The production host must serve
`index.html` for the three approved SPA route patterns.
**Consequences**: React Router and `frontend/vercel.json` are approved for this
task. The existing backend API, database schema, collection pipeline, wording
policy, and Vercel project root remain unchanged. No deployment is performed by
TASK-054.

**Follow-up decision (2026-07-10)**: Supersede only ADR-036's Home composition
of one featured issue plus four unique compact rows. Home now defaults to the
7-day window and uses one shared absolute-change ranking: the featured issue is
rank 1 and appears again in a top-five ranking table. Add a direction summary
whose ratio denominator is upward plus downward issues only, and replace each
category's largest-change value with the simple arithmetic mean of valid
selected-window changes. The existing routes, `/issues` 24-hour default,
client search, detail loading boundaries, public API, schema, dependency set,
and scoped Vercel configuration remain unchanged.

---

### ADR-037: Close Day 5 on verified technical MVP scope and defer release operations

- **Date**: 2026-07-10
- **Status**: Accepted
- **Decided by**: User / PM Planner

**Context**: Day 5 runtime work and integration review were complete, but the
latest `main` still failed Frontend TypeScript validation because TASK-054 used
`Array.prototype.at()` under the existing `ES2020` library. Deployment, final
presentation production, screenshots, rehearsal, and backup capture were also
unfinished and remained separately approval-gated or operational work.

**Decision**: Fix only the ES2020 compatibility blocker in PR #53, verify the
full Frontend build path and Backend regression suite, and close Day 5 as a
technical MVP implementation/review milestone. Move deployment to `TASK-020`
and final presentation/rehearsal/capture work to `TASK-021`. Do not describe
those deferred deliverables as completed.

**Rationale**: The core product flow and v3 report path have implementation and
review evidence. The remaining work does not change the technical MVP and can
resume independently without obscuring the actual build status.

**Trade-offs**: The closeout does not provide a hosted service, final deck,
final screenshots, rehearsed presentation, backup recording, or a workflow run
from the eventual merged PR #53 revision. The repair and closeout record also
remain outside `main` until PR #53 passes normal review and merge.

**Consequences**: `roadmap.md` marks Day 5 complete with an explicit deferred
deliverables list, `tasks/backlog.md` retains TASK-020/TASK-021 as follow-up,
and `reports/day-5-closeout.md` is the evidence record. No deployment,
dependency, schema, API, infrastructure, database, provider, copy-policy, or UI
behavior change is approved by this decision.

---

### ADR-038: Approve verified automated context and evidence-grounded v4 reports

- **Date**: 2026-07-11
- **Status**: Accepted ⚠️ HUMAN APPROVAL
- **Decided by**: User (human), PM / Planner recording

**Context**: TASK-055 proposed a sequential TASK-056~065 program that replaces
the frozen v3 manual-only context path with a narrowly bounded automated
research, verification, evidence, report, API, and change-episode UI flow. The
project constitution required explicit approval for the policy change, schema,
public API, paid provider use, and database writes before implementation.

**Decision**:

1. Authorize TASK-056~065 sequentially. TASK-056 is the policy/contract gate;
   TASK-057~065 must follow the dependencies and stop conditions in
   `reports/task-055-automated-context-execution-plan.md`.
2. Permit automated context only when every source URL comes from an OpenRouter
   API `url_citation` annotation, deterministic hard gates pass, a research
   model and a different verifier model agree, and the candidate is stored as
   `verified`. Model-body URLs and non-verified candidates are never public.
3. Permit OpenRouter research, independent-verification, and report-writing
   calls for this program up to USD 100 cumulative usage. Usage must be
   recorded per run without secrets, prompts, or full responses, and execution
   must refuse work that would exceed the remaining approved budget.
4. Permit one new append-only migration,
   `backend/migrations/002_context_candidates.sql`, adding
   `context_candidates` and `context_collection_runs`. Existing migrations,
   `related_events`, and legacy `ai_reports` rows remain unchanged.
5. Permit the strict v4 response on the existing
   `GET /api/issues/{id}/report` path with top-level report timing, episode,
   evidence references, and verified context candidates with source metadata.
   Legacy v1-v3, failed, malformed, unverified, and evidence-inconsistent rows
   must return the existing not-yet-generated state.
6. Fix v4 content to exactly `issue_overview`, `observed_change`,
   `context_summary`, `relationship_boundary`, `what_to_check`,
   `data_limitations`, and `caution_note`. `context_summary` alone is nullable.
   Metric sentences require stored metric evidence; context sentences require
   stored verified-candidate evidence.
7. Permit the TASK-063 change-episode UI and local/development-only candidate,
   report, migration, backfill, and audit writes. Production DB writes,
   deployment, infrastructure changes, unrelated schema/API changes, and new
   dependencies remain outside this approval.
8. Preserve the bans on relationship assertions, real-world result
   assertions, action-inducing language, individual-participant data, and
   open-ended analysis. A missing or inconsistent requirement fails closed.

**Rationale**: The program adds current public context while preserving the
product's evidence-first, non-predictive posture through mechanical provenance,
independent verification, strict evidence IDs, and verified-only public reads.

**Trade-offs**: Automated verification can legitimately yield no public
candidate. Provider cost and availability become pipeline dependencies, so the
last successful candidate/report remains live on failure and `no_candidate`
is a normal outcome. v3 remains the historical MVP contract while v4 is built.

**Consequences**: TASK-056~065 move to `tasks/active.md`. TASK-057 and TASK-058
may start only after TASK-056 documentation passes. TASK-065 may call the
provider and write only against a guarded local/development database within
the cumulative USD 100 limit. Deployment remains a separate approval gate.

---

### ADR-039: Context evidence duplicates are episode-scoped and market deletion cascades

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Backend Implementer within ADR-038 schema approval

**Context**: TASK-057 required a deterministic duplicate-evidence rule and
documented delete behavior for the two append-only v4 context tables.

**Decision**: Enforce uniqueness on
`(market_id, episode_at, evidence_hash)`. A duplicate insert is an idempotent
skip: callers keep the existing row and never update it. The same citation
bundle may support a different market or a different episode. Both new tables
use `ON DELETE CASCADE` from `markets`, matching the lifecycle of all existing
market-owned tables in `001_initial_schema.sql`.

**Rationale**: Episode-scoped uniqueness prevents duplicate batch writes while
preserving legitimate reuse across issues or later episodes. Consistent cascade
behavior avoids orphaned audit rows and matches the accepted initial schema.

**Consequences**: TASK-060 must catch duplicate-integrity errors as skips, not
rewrite candidates. A parent-market delete removes its candidate and run rows;
normal batch paths remain strictly insert-only.

---

### ADR-040: OpenRouter server-tool research trusts annotations, not model URLs

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Data/AI Implementer within ADR-038 provider approval

**Context**: TASK-058 needed to reconcile OpenRouter's beta
`openrouter:web_search` Chat Completions response with the v4 citation-ID
contract. The model can copy URLs into JSON, but model text alone is not
provenance.

**Decision**: Send the server tool through the existing OpenAI-compatible SDK
using OpenRouter-only `extra_body.tools`. Parse nested or flat
`url_citation` annotations, normalize and hash only those URLs/excerpts, and
map model-returned candidate URLs to citation IDs only on exact annotation URL
matches. Discard candidates with no matching annotation. Require provider
usage to show a server-tool search unless it is a completed empty search, cap
reported searches at six and total citations at 30. ADR-047 amends only the
reported-query check: queries use deterministic market-metadata suggestions as
scope anchors and must pass normalized topic/entity overlap.

**Rationale**: The model can organize candidate drafts but cannot create
evidence. Exact annotation matching preserves provenance and lets TASK-059
apply canonicalization and substantive verification independently.

**Consequences**: Model-body URLs, missing-title/invalid-scheme annotations,
out-of-scope queries, over-limit usage, and malformed output fail closed.
No DB write occurs in TASK-058; TASK-059 receives normalized citations and
candidate drafts only.

---

### ADR-041: Deterministic gates control publication before independent verification

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Data/AI Implementer within ADR-038 policy approval

**Context**: TASK-059 needed a reproducible publication boundary that could not
be overridden by either the research model or verifier model.

**Decision**: Canonicalize URLs and reject unsafe forms; require timezone-aware
episode/event dates supported by citation text and compatible with the search
window; require matched entities in both market metadata and evidence; require
tracked-condition token support; reject unsupported English proper nouns,
conflicting dates, relationship/result assertions, and missing annotations.
Accept the deterministic source path only when one configured/resolution/
government-family official source directly supports the candidate, or at least
two distinct publisher families with distinct content hashes and normalized
content directly support it. Verify at most five of at most eight rule-passing
candidates in one call, using a different OpenRouter provider family with no
web tool. Any disagreement, extra claim/date/name, missing candidate, malformed
response, or unsafe summary remains non-public.

**Rationale**: Model judgment is useful only after provenance and support are
mechanically established. Provider-family separation and no-search verification
reduce correlated generation and prevent the verifier from inventing new
evidence.

**Consequences**: TASK-060 may persist every decision for audit but may pass
only `verification_state="verified"` candidates to v4 report generation. Hard
failures are `rejected`; capacity or verifier failures are `withheld` or batch
failures. Fixed-fixture decisions are deterministic.

---

### ADR-042: Context batch is per-market append-only and budget-reserved

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Data/AI Implementer within ADR-038 execution approval

**Context**: TASK-060 needed to add paid-capable research to the scheduled
batch without letting one market failure, duplicate evidence, or provider cost
damage the existing pipeline.

**Decision**: Select targets by current-run signal, absolute 24-hour change,
top-10 heat, or missing/stale verified context; backfill may select every latest
eligible metric. Run research and verification in one isolated market unit,
store all audit decisions append-only, return only verified candidate IDs, cap
public candidates at three, and record `no_candidate` as a normal completion.
Treat duplicate market/episode/evidence rows as idempotent references to the
existing row. Persist secret-free research/verifier usage and errors per run.
Before every market, sum recorded research/verifier/writer costs and skip the
call when current spend plus the configured reservation would exceed the
ADR-038 USD 100 cap. The scheduled order is signals → context → reports.

**Rationale**: Market isolation preserves last-known-good context and reports,
while append-only audit rows make cost and publication decisions reproducible.
Pre-call reservation keeps the program inside the approved external-call
boundary even before TASK-065 performs a live run.

**Consequences**: Context failure makes the combined log partial but does not
block other markets or the existing report stage. TASK-061 must consume only
verified stored candidates and add writer usage to the same cumulative budget
accounting boundary.

---

### ADR-043: V4 reports split model-authored prose from deterministic evidence

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Data/AI Implementer within ADR-038 execution approval

**Context**: TASK-061 had to produce useful Korean summaries while preventing
the writer model from changing metrics, introducing unsupported context, or
weakening the approved relationship and caution boundaries.

**Decision**: Give the writer only structured metric inputs and at most three
same-episode verified candidates. Allow its strict response to contain exactly
`issue_overview` and `what_to_check`; assemble `observed_change`, nullable
`context_summary`, `relationship_boundary`, `data_limitations`, and
`caution_note` deterministically. Store an internal v4 envelope containing the
seven-field content, one `metric:{id}` reference, zero to three
`candidate:{id}` references, and the matching candidate-ID list. Reject
missing sources, field/reference mismatches, unknown evidence, unsafe
relationship/result/action phrasing, model-authored URLs, and unsupported
numbers. Keep v1-v3 and failed rows append-only for audit but do not let them
block v4 regeneration. Record writer token/cost usage and reserve cost before
each call under the shared USD 100 cap.

**Rationale**: Deterministic evidence-bearing sentences make stored output
reproducible and independently checkable, while retaining a narrow model role
for readability. The envelope lets TASK-062 verify the stored row against DB
state rather than trusting prose alone.

**Consequences**: No verified candidate produces `context_summary=null` and no
candidate reference. A context-stage failure skips only that market and
preserves the prior successful v4 row. TASK-062 must expose only envelopes
whose metric timestamp, episode, candidate state, sources, and evidence
references all still validate.

---

### ADR-044: V4 report reads revalidate the stored evidence bundle

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Backend Implementer within ADR-038 execution approval

**Context**: A successful stored v4 row is not sufficient by itself for public
output. TASK-062 had to prevent stale legacy shapes, altered JSON, missing
candidate rows, non-public verification states, and source-field drift from
crossing the read boundary.

**Decision**: Query only successful `prompt_version="v4"` rows joined to a
metric belonging to the requested issue, load the latest snapshot at or before
that metric, and load only verified candidates. Strictly parse the internal
envelope, resolve its ordered candidate IDs, require same-market and exact
episode linkage, validate every stored internal source field, and reconstruct
all deterministic content from DB values. Return the report only when the
reconstruction, semantic checks, evidence-reference order, source URL/domain,
and `data_as_of`/episode timing all match. Public source output includes only
title, URL, domain, nullable publication time, and source type. Static fallback
and v1-v3/failed/malformed/missing-evidence rows return the accepted 200 empty
state; unknown issues remain 404.

**Rationale**: Revalidation makes the read API an independent fail-closed
boundary rather than assuming that append-only storage can never be incomplete
or altered. Deriving the public source object from the validated stored record
also prevents internal audit fields from leaking.

**Consequences**: The Frontend must consume only report version v4 in TASK-063.
Until migration and backfill run in TASK-065, development data with only v3
rows naturally shows the neutral not-yet-generated state. No API request calls
an external provider or writes to the database.

---

### ADR-045: V4 renders as one evidence-first change episode

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Frontend Implementer within ADR-038 execution approval

**Context**: The v3 one-section-at-a-time navigator separated metrics, context,
limitations, and caution. TASK-063 needed to make their linkage visible without
turning context into an explanation of the observed movement.

**Decision**: Render one change-episode card in this order: issue overview,
observed change, optional same-review-window public context with candidate and
source cards, mandatory relationship boundary, later checks, data limitations,
and interpretation caution. Hide the whole context region when no verified
candidate exists. Give each candidate card and its nearest visible chart marker
the same candidate ID and bidirectional anchors. Open approved public source
URLs in a new tab with `noopener noreferrer`. Repeat strict v4 schema, timestamp,
evidence-reference, candidate/source, URL/domain, and no-internal-field checks
in the Frontend parser. Keep local-host-only 0/1/3 candidate fixtures for
responsive verification; they are inaccessible on non-local hosts.

**Rationale**: A single reading flow makes the evidence hierarchy legible while
the explicit relationship boundary and marker note prevent temporal proximity
from being presented as influence. Repeating parser checks gives malformed API
payloads a fail-closed UI state.

**Consequences**: Legacy v3 success payloads enter the report error state and
are never partially rendered. TASK-064 must review candidate/marker linkage,
source-link safety, null-context behavior, all three responsive widths, and the
content-safety wording of the complete integrated flow.

---

### ADR-046: Normalize v4 writer evidence timestamps to UTC before assembly

- **Date**: 2026-07-11
- **Status**: Accepted
- **Decided by**: Reviewer within ADR-038 execution approval

**Context**: TASK-064's full-flow SQLite fixture produced a valid verified
candidate and v4 row, but the API correctly withheld it because the writer had
serialized a timezone-naive snapshot timestamp while the read boundary
reconstructed the same evidence as UTC-aware. SQLite does not preserve timezone
metadata on these columns; PostgreSQL does.

**Decision**: Normalize v4 snapshot, episode, candidate-event, and end-date
inputs to UTC-aware datetimes in `build_v4_inputs_for_market` before any
deterministic sentence or stored envelope is assembled. Keep the API's UTC
normalization and exact reconstruction check unchanged.

**Rationale**: Stored deterministic content must be identical across the
approved local SQLite test path and development PostgreSQL path. Fixing the
writer input is safer than weakening the API's independent evidence check.

**Consequences**: Local/development v4 rows now round-trip through the strict
API, and the full-flow integration test prevents regression. No schema, public
API, dependency, provider, infrastructure, or deployment boundary changed.

---

### ADR-047: Permit bounded server-tool query reformulation within metadata scope

- **Date**: 2026-07-11
- **Status**: Accepted ⚠️ HUMAN APPROVAL
- **Decided by**: User, Data/AI Implementer + PM / Planner

**Context**: The approved development migration succeeded, but bounded live
preflights showed that current OpenRouter server tools generate or reformulate
search queries. Valid annotated responses therefore fail ADR-040's exact
model-reported-query membership check. Multiple current model families,
one-query configuration, explicit prompt constraints, and exactly one retry did
not produce a reliable path.

**Decision**: Retain deterministic metadata suggestions, query/result
caps, annotation-only evidence, deterministic verification, independent
provider verification, verified-only storage/API reads, and all wording/evidence
checks. Replace exact query-string membership with a bounded-count and
normalized market-metadata overlap check, while storing the reported strings
for audit.

**Rationale**: OpenRouter documents that the model creates the server-tool
query. Exact equality is not an enforceable client-side constraint on this
provider behavior; annotation provenance and candidate hard gates remain the
actual publication boundary.

**Consequences**: Every reported query must be non-empty, unique, at most 300
characters, within the six-query cap, and share normalized distinctive
topic/entity tokens with title, description, category, or tracked condition.
Generic search vocabulary, dates, and domains cannot make an unrelated query
pass alone. Exact reported query strings remain stored for audit. Annotation
provenance and every downstream candidate/publication gate are unchanged.
Migration 002 and existing audit rows remain in the approved development DB;
deployment and production writes remain excluded.

**Implementation result**: TASK-065 completed exactly 50 development backfill
targets. Forty-six distinct issues reached a normal completed research state;
reported query/result maxima were five and 26. Seven drafts failed existing
candidate gates, zero candidates became public, and no gate was relaxed.
Final evidence is in `reports/task-065-context-backfill-evaluation.md`.

---

### ADR-004: Monorepo, npm + pip, GitHub Actions

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User (via harness setup interview)

**Context**: Technical Design left repo structure, package manager, and CI/CD undecided.
**Decision**: Single monorepo (`/frontend`, `/backend`); npm for frontend, pip for backend; GitHub Actions for the batch-collector schedule and basic lint/test.
**Rationale**: Minimizes cross-repo coordination overhead for a 4-person/5-day build; npm/pip are the zero-setup defaults for their respective ecosystems.
**Trade-offs**: Frontend and backend deploy to different platforms (Vercel vs Railway/Render) despite sharing a repo — requires each platform's build config to target the correct subfolder.
**Consequences**: `commands.md` and `tech-stack.md` assume this layout; Day 1 setup must configure both platforms' root-directory settings accordingly.

---

### ADR-005: Role-prefixed task branches and active-task assignment format

- **Date**: 2026-07-07
- **Status**: Accepted
- **Decided by**: User / PM

**Context**: The harness expects the PM to organize scope and route work to each role, but task selection and branch setup were still manual and easy to drift from.
**Decision**: Add a role-prefixed branch policy, require `Owner`, `Assignee`, `Branch`, and fixed `Status` values in `tasks/active.md`, and document preview-only automation script designs for assignment/start-task flows.
**Rationale**: Keeps role ownership, task IDs, and branch names aligned before implementation starts, while preserving human approval for file writes and git operations.
**Trade-offs**: Adds a small process step before coding starts.
**Consequences**: Agents must choose only assigned work from `tasks/active.md`, confirm the listed branch before starting, and never commit directly to `main` or `master`.

---

### ADR-006: Day 1 active work limited to P0 kickoff tasks

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 1 needed role-by-role assignment without expanding hackathon scope or blocking frontend work on backend/data availability.
**Decision**: Move `TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, and `TASK-011` into `tasks/active.md`; keep `TASK-007` in backlog until the Polymarket field/rate-limit spike validates the data shape.
**Rationale**: These tasks map directly to PRD §14 Day 1 deliverables: screen structure, API contract, sample data, scope lock, and presentation key messages.
**Trade-offs**: Backend has several small Day 1 tasks, so sequencing matters: scaffold and health endpoint first, then contract/schema draft.
**Consequences**: Each role has a concrete branch and Day 1 Definition of Done; schema application remains behind the human-approval gate in `AGENTS.md`.

---

### ADR-007: Backend Day 1 scaffold — Postgres driver, env loading, migration tooling

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: User (via human approval) / Backend Implementer

**Context**: `dependencies.md` pre-approved SQLAlchemy as the ORM but not a concrete Postgres driver package, and did not cover local `.env` loading or a migration-file format. TASK-001/TASK-002 needed these to produce a runnable scaffold and schema draft.
**Decision**: Use `psycopg[binary]` (psycopg3) as the Postgres driver and `python-dotenv` for local-dev `.env` loading only (both human-approved 2026-07-08, recorded in `dependencies.md`). Write the TASK-002 schema draft as plain SQL (`backend/migrations/001_initial_schema.sql`) rather than adopting a migration framework (e.g. Alembic), since the migration-tool choice is still an open Day 1 decision per `commands.md` and adopting one is a separate dependency decision from drafting the schema itself.
**Rationale**: Keeps the scaffold unblocked without pre-empting the still-open migration-tool decision; psycopg3 is actively maintained and works with both sync and future async SQLAlchemy engines.
**Trade-offs**: `commands.md`'s example commands (`alembic upgrade head`) don't match the current migration mechanism (`psql -f migrations/001_initial_schema.sql`) until the tool decision is made — flagged, not yet reconciled.
**Consequences**: `backend/migrations/001_initial_schema.sql` and the mirrored SQLAlchemy models in `backend/app/db/models.py` are draft-only and unapplied; applying them to any database still requires a separate human-approval step per `AGENTS.md`.

---

### ADR-008: `/api/issues/:id/report` not-yet-generated response uses 200, not 204

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Frontend Implementer / Backend Implementer

**Context**: Technical Design §5 specifies returning HTTP `204` with a JSON body hint `{"status": "not_yet_generated"}` when no AI report exists yet for an issue. HTTP `204 No Content` cannot carry a response body per spec — most clients discard it, so the frontend would never see the hint.
**Decision**: TASK-003's draft contract (`backend/API_CONTRACT.md`) instead returns `200 OK` with `{"status": "not_yet_generated"}`, keeping the same neutral-empty-state intent without the invalid HTTP semantics.
**Rationale**: Preserves the product intent (no error state; frontend shows a neutral placeholder) while fixing a factual protocol error in the source spec.
**Trade-offs**: Diverges from the literal Technical Design wording, so Technical Design §5 should be interpreted through this ADR for the report-empty response.
**Consequences**: Day 2 frontend/backend integration should treat `200 OK` with `{"status": "not_yet_generated"}` as the canonical no-report-yet response. If this ever changes, update `backend/API_CONTRACT.md`, `backend/app/schemas/issues.py::ReportNotYetGenerated`, and the corresponding route/tests together.

---

### ADR-011: Day 1 DB schema draft accepted, unapplied

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Backend Implementer

**Context**: Day 1 required a database schema artifact so Day 2 data pipeline and read API work can align on table boundaries, but `AGENTS.md` requires human approval before applying schema changes to any shared or production database.
**Decision**: Accept `backend/migrations/001_initial_schema.sql` and `backend/app/db/models.py` as the Day 1 schema draft artifact. The schema remains unapplied; applying it to any shared or production database is a separate approval-gated action.
**Rationale**: The draft includes the required MVP tables, preserves the append-only snapshot/metric strategy, and does not introduce `users`, `watchlists`, wallet-level, or participant-level tables.
**Trade-offs**: The schema has not yet been validated against a live hosted Postgres instance, and the migration-tool choice remains plain SQL for now rather than Alembic.
**Consequences**: `TASK-002` can close as "draft accepted, unapplied." Day 2 implementation may align to the draft shape, but any future schema correction must respect the project rule to append new migration changes rather than editing applied migration history.

---

### ADR-012: Day 2 active work limited to P0 data path, core API, and dashboard integration

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 1 closed with a working frontend dummy flow, accepted mock API contract, accepted-unapplied schema draft, and validated Polymarket field samples. The next risk is spreading Day 2 effort across attractive P1 work before the real data path reaches the dashboard.
**Decision**: Complete `TASK-031` for Day 2 allocation, then assign Day 2 active implementation work to `TASK-007`, `TASK-008`, `TASK-009`, `TASK-010`, and `TASK-012` only. Keep category filtering, `/api/signals` feed, volatility/attention metrics, report generation, event candidates, deployment, and copy-polish passes deferred until the P0 data/API/dashboard path is usable.
**Rationale**: This matches PRD §14's Day 2 deliverables: dashboard v1, ranking API, change-calculation data, and candidate issue list for the demo. It also preserves the PRD §13.1 operating principle that frontend, backend, and data work can proceed in parallel as long as the contract and handoff order stay explicit.
**Trade-offs**: Some visible polish and richer metrics remain idle even if they would improve the demo surface. The team may need a follow-up Day 2/3 bridge if live metric data arrives late.
**Consequences**: `tasks/active.md` is the Day 2 source of execution truth for implementation, `tasks/completed.md` records `TASK-031`, `tasks/backlog.md` no longer lists the moved Day 2 tasks, and `reports/day-2-work-allocation.md` records the sequence. Applying the schema draft to any shared or production database remains a separate human-approval gate.

---

### ADR-009: TASK-005 frontend uses local state and dummy issue contract

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Frontend Implementer

**Context**: The frontend needed a usable dashboard/detail flow before the backend API is ready.
**Decision**: Implement dashboard-to-detail navigation with React local state and a typed dummy issue data contract under `frontend/src/data`.
**Rationale**: This matches the Day 1 instruction to proceed without waiting for the API and avoids adding a router dependency.
**Trade-offs**: Browser URL state is not shareable yet; the API integration pass will need to replace the dummy source.
**Consequences**: Frontend and backend can align on the `Issue` shape while preserving the P0 demo flow.

---

### ADR-010: PR #6 audit risk is temporarily accepted without a Vite major upgrade

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: User / Frontend Implementer

**Context**: PR #6 originally cleared `npm audit` by moving the frontend build stack to Vite 8, but that crossed a major-version boundary and triggered the `dependencies.md` approval gate. Reverting to the approved Vite 5.x range restores the project-approved dependency policy but leaves `npm audit` reporting Vite/esbuild development-server advisories.
**Decision**: Keep PR #6 on the approved Vite 5.x / `@vitejs/plugin-react` 4.x major ranges and temporarily accept the dev-server audit warning for this PR. Do not reintroduce the Vite major upgrade in PR #6.
**Rationale**: The PR's scope is dashboard/detail UI against dummy JSON. A major build-tool upgrade is broader than the feature and requires explicit approval plus full manual demo-flow retest. The reported advisories affect the dev-server/tooling path rather than the generated static production bundle.
**Trade-offs**: `npm audit` remains non-zero until a separately approved Vite major upgrade lands.
**Consequences**: PR #6 can be reviewed for merge based on build/lint/copy-safety checks, with `npm audit` recorded as an accepted temporary risk. A future dependency-maintenance task should request approval for the Vite major upgrade and perform the required manual demo-flow retest.

---

### ADR-013: `/api/issues` degrades to `200` + static fallback, not `503`, when live data is unavailable

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Backend Implementer; confirmed by User / PM gate on 2026-07-08

**Context**: `TASK-010` wired `/api/issues`, `/api/issues/:id`, and `/api/issues/:id/history` to real Postgres reads via `app/db/session.py::get_db()`. As of this task, `TASK-007`/`TASK-008` had not produced any `market_snapshots`/`market_metrics` rows, and `DATABASE_URL` is also commonly unset in local dev. Technical Design §5 mentions `503` for a "degrade to last-known-good data" case, which is ambiguous about whether the response body is still served on a `503`.
**Decision**: When `DATABASE_URL` is unset, a live query fails, or `market_snapshots` has zero rows, the affected endpoints return `200` with the existing static sample dataset (`_FALLBACK_ISSUES` in `app/api/routes/issues.py`) and its fixed `data_as_of`, not `503`. Every fallback is logged via `logger.warning("FALLBACK: ...")` with the specific reason, so it can never become a silent permanent substitute once real data lands.
**Rationale**: Matches `reports/day-2-work-allocation.md`'s Judging Q&A seed ("the API and frontend keep a static/last-known-good fallback path with honest timestamps") and `TASK-012`'s DoD ("retain a static fallback for demo resilience") - a `503` would force the frontend into an error state instead of a usable demo dashboard.
**Trade-offs**: `503` as specified in Technical Design §5 is not implemented; if a future need arises to distinguish "serving fallback data" from "serving live data" at the HTTP layer (e.g. for monitoring), that will require either a new response field (contract change, needs approval) or an out-of-band signal (e.g. a response header), not implemented here.
**Consequences**: `backend/API_CONTRACT.md`'s Error shape section now documents this instead of the "not yet triggerable" `503` placeholder. The PR #10 `CHANGES_REQUESTED` blocker for explicit confirmation is resolved by the 2026-07-08 user/PM-gate follow-up; no response schema change is needed.

---

### ADR-014: TASK-007 normalized artifacts omit raw source descriptions

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Data/AI Implementer, following PR #9 review feedback

**Context**: PR #9 review found that `normalized_samples.json` exposed raw external descriptions under the top-level `description` field, and some records had null required downstream fields such as `volume_24h` or `end_date`.
**Decision**: The batch collector now emits a display-safe `description: str` generated by the collector, omits raw source descriptions from the sample artifact, and records `source_metadata.description_policy = raw_source_descriptions_omitted`. Candidate records missing required downstream fields are skipped with structured reasons in `skipped_records.json`.
**Rationale**: TASK-008/TASK-010 need a stable handoff contract, while fallback/display consumers must not accidentally render raw external source text.
**Trade-offs**: The sample description is intentionally generic until a later, policy-reviewed description-generation path exists.
**Consequences**: The refreshed 50-record `normalized_samples.json` has no null required fields, all top-level descriptions are strings, and invalid candidates are quarantined rather than producing partial normalized records.

---

### ADR-015: TASK-008 bootstraps `markets`/`market_outcomes` rows and ships a P0-only metric set

- **Date**: 2026-07-08
- **Status**: Accepted
- **Decided by**: Data/AI Implementer

**Context**: Technical Design §6 steps 3-5 (`app/core/snapshot_metrics.py`) need a stable `markets.id` UUID to write `market_snapshots`/`market_metrics` rows against, but TASK-007's normalize step (steps 1-2) never touches the database - it only produces normalized dicts/JSON, confirmed by `collector.py` having zero SQLAlchemy imports. No other task in `tasks/active.md` claims ownership of populating `markets`/`market_outcomes` from normalized data. Separately, Service Design §5's metric table marks `change_24h`, `change_7d`, the simplified "market confidence score," and the simplified "issue heat score" as P0, while `volatility_score`, `attention_score`, and a `caution_low_activity`/`caution_high_volatility` confidence split are P1 or an open design question (`known-issues.md`'s "Minimum volume/liquidity floor" item).
**Decision**: (1) `snapshot_metrics.py` does a minimal get-or-create of `markets` (by `polymarket_condition_id`) and its one tracked `market_outcomes` row as plumbing inside steps 3-4, updating only `markets.last_seen_at`/`status` in place (the one exception to append-only per §4.10) - no new table or column. (2) `market_metrics.confidence_level` is populated with only `sufficient`/`insufficient_data` this task; `caution_low_activity`/`caution_high_volatility` are left unused pending the open volume/liquidity-floor decision. (3) `heat_score` uses a placeholder bounded formula (`|change_24h| * 500 + min(volume_24h / 50, 30)`, capped at 100); `volatility_score`/`attention_score` are always `null` (P1, not computed).
**Rationale**: Building markets/outcomes rows here is the only place in the current step 1-8 pipeline where it can happen without inventing a new task; it satisfies the existing schema's FK contract rather than adding a feature. Withholding `caution_low_activity` avoids fabricating an un-approved policy threshold under the project's no-fabrication rule, applied to thresholds as well as data. The heat_score formula is explicitly sanctioned as a starting point by Service Design §5 ("can start as a simple weighted rank... don't need full composite v1") and by `known-issues.md`'s existing "heat_score weighting formula - start simple, tune once real data is visible" note.
**Trade-offs**: `confidence_level` currently only distinguishes "have a 24h change" from "don't" - it does not yet flag a technically-sufficient-history market that's actually low-volume/thin or high-volatility. `heat_score` values are not yet tuned against real batch behavior.
**Consequences**: TASK-009's `±5pp` threshold detector can rely on `change_24h` as implemented. A future task should resolve the volume/liquidity floor open question and add `volatility_score` before `caution_low_activity`/`caution_high_volatility` can be populated - tracked in `known-issues.md`.

---

### ADR-016: TASK-009 signal detection reads `market_metrics` by `computed_at`, decoupled from TASK-008's run function

- **Date**: 2026-07-08
- **Status**: Accepted (implementation-scope note, not a policy/threshold/schema change - no human approval gate applies)
- **Decided by**: Data/AI Implementer

**Context**: Technical Design §8 step 6 (signal detection) runs immediately after step 5 (metrics) computes each market's `change_24h` in the same batch pass. TASK-008's `run_snapshot_and_metrics()` (`app/core/snapshot_metrics.py`) already computes and inserts `market_metrics` rows for a run, but its return type (`BatchRunResult`/`MarketRunOutcome`) does not carry the inserted `MarketMetric.id` or the row objects themselves - only a summary (`change_24h`, `confidence_level`, etc.) per market.
**Decision**: `app/core/signal_detection.py` does not modify TASK-008's return type or call signature. Instead, `detect_signals_for_run(db, run_timestamp)` re-queries `market_metrics` for rows where `computed_at == run_timestamp` (the same timestamp `run_snapshot_and_metrics` already stamps every row in a run with), then evaluates each against the ±5pp threshold.
**Rationale**: Keeps TASK-008's already-reviewed/merged module untouched (lower regression risk) while still giving step 6 exactly the metrics computed in "this run." The two modules compose via `detect_signals_for_run(db, run_snapshot_and_metrics(...).run_timestamp)` without any shared-object coupling.
**Trade-offs**: One extra `SELECT` per run instead of reusing in-memory objects from step 5; at hackathon scale (30-50 markets, a handful of runs/day) this is not a performance concern. `issue_signals.detail` therefore stores `metric_id`/`change_24h`/`threshold` rather than the bounding `market_snapshots` ids mentioned as an example in Technical Design §4.5, since TASK-008 doesn't expose the reference snapshot id used inside `compute_change_for_window` - the schema's `detail` field is explicitly "free-form extra context," not a fixed contract, so this is populated with what's actually available rather than fabricated.
**Consequences**: A market's `expectation_shift` signal can be traced back to its exact `market_metrics` row via `detail.metric_id`. If a future task needs snapshot-id-level detail, `compute_change_for_window` in `snapshot_metrics.py` would need to additionally return the reference snapshot's id - not done here to avoid touching TASK-008's merged module for a need this task doesn't have.

---

### ADR-017: Day 3 active work limited to detail, chart, and caution-badge readiness

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 2 closed with a usable data/API/dashboard baseline. PRD §14 defines Day 3 as the detail screen, chart, tooltip, inflection-point markers, and interpretation-caution badge day, while template summary generation belongs to the Day 4 demo-flow milestone.
**Decision**: Open Day 3 active work for `TASK-013`, `TASK-014`, `TASK-017`, `TASK-035`, and `TASK-036`. Treat `TASK-015` as deferred until the detail/chart/badge path is stable, unless PM explicitly reassigns it late in Day 3.
**Rationale**: The highest current demo risk is a detail view that shows a chart or caution badge in a confusing way. Stabilizing that path first protects the core Home -> Detail -> Chart flow before adding the template summary generator.
**Trade-offs**: Data/AI report work may start later than the original `TASK-015` Day 3-4 range suggests. This keeps the team from splitting attention before the core detail path is trustworthy.
**Consequences**: `tasks/active.md` is the Day 3 source of execution truth; `reports/day-3-work-allocation.md` records the sequence and guardrails. Shared/dev database schema application, public API response-shape changes, new dependencies, deployment work, and wording-policy changes remain approval-gated by `AGENTS.md`.

---

### ADR-018: Detail chart windows require baseline-covered history

- **Date**: 2026-07-09
- **Status**: Accepted (TASK-013 implementation decision)
- **Decided by**: Frontend Implementer

**Context**: The Day 3 detail chart must support 24h, 7d, and 30d selection with honest insufficient-history states. The existing frontend sliced the last 2/8/31 points and displayed `change30d ?? change7d`, which could make a short history look like a valid longer-window chart.
**Decision**: For each selected chart window, the frontend now requires at least one history point at or before that window's baseline plus a later point before rendering a line chart. If that baseline is unavailable, the chart shows an insufficient-history state. The 30d metric displays only an actual 30d history-derived change, not a 7d fallback.
**Rationale**: This matches the no-fabrication rule used by backend metrics and avoids overstating sparse API/fallback history during the demo.
**Trade-offs**: A window may show an insufficient-history state even when it has several recent points, if those points do not reach the requested baseline. This is preferable to stretching a shorter span into a longer-window interpretation.
**Consequences**: `frontend/src/utils/history.ts` is the shared frontend helper for window coverage. The detail chart still preserves the accepted API response shape and uses API-provided `signals` when present, with local adjacent 5pp detection only as a fallback marker source.

---

### ADR-019: Caution-badge thresholds and expectation-shift marker handoff (TASK-036)

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: Data/AI Implementer

**Context**: MVP interpretation caution logic needs to handle `caution_low_activity` and `caution_high_volatility` without waiting for a complex volume/liquidity floor calculation, and `expectation_shift` markers need a clear consumption contract.
**Decision**:
1. **Caution Thresholds**: Implemented conservative hardcoded thresholds in `compute_confidence_level` based on sample data: 500 USDC for `volume_24h`, 1000 USDC for `liquidity`, and >15pp absolute change for `change_24h`.
2. **Precedence**: `insufficient_data` continues to take precedence over any activity or volatility caution state if history is lacking.
3. **Marker Consumption Contract**: The backend `/api/issues/:id` endpoint will query `issue_signals` for any `expectation_shift` (±5pp threshold, medium severity) rows related to the market. The frontend will consume these rows to render "Expectation Shift" visual markers on the detail chart at the `triggered_at` timestamps, enabling users to visually align shifts with their own context without implying causation.
**Rationale**: Uses the existing schema and Enum values for `confidence_level` without adding new schema fields, keeping the MVP lightweight. Documenting the marker contract ensures frontend/backend alignment without extending P1 metrics.
**Trade-offs**: Hardcoded thresholds may need adjustment as real-world Polymarket volume changes, and using absolute 24h change as a volatility proxy is less precise than a full `volatility_score`.
**Consequences**: Closes MVP path for TD-008. Backend and frontend implementers can proceed with API/UI integration for caution badges and expectation-shift markers.

---

### ADR-020: Day 4 active work limited to summary and demo-flow completion

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: PM / Planner

**Context**: Day 3 closed the detail/chart/caution path, and latest
`origin/main` at `af83f7e` includes the Day 3 closeout merge. PRD section 14
defines Day 4 as template summaries, demo-flow completion, fallback readiness,
manual event candidates, and a deck/script draft.
**Decision**: Open Day 4 active work for `TASK-015`, `TASK-039`, `TASK-016`,
`TASK-019`, `TASK-040`, and `TASK-018`. Keep P1 category/feed/extra-metric
work deferred until the Day 4 P0 path is complete. Treat any paid external AI
provider call, schema change, deployment, infrastructure change, public API
shape change, or shared/production database write as approval-gated.
**Rationale**: The remaining demo risk is not feature breadth; it is whether
the Home -> Detail -> Chart -> Summary path is coherent, safe, and rehearsable.
This sequence lets Data/AI and Backend unblock Frontend report display while PM
prepares the demo story and final wording pass.
**Trade-offs**: General UI polish and P1 metrics remain deferred even though
they could improve perceived quality. The allocation prefers a complete and
guarded summary/demo path over broader scope.
**Consequences**: `tasks/active.md` is the Day 4 execution source of truth, and
`reports/day-4-work-allocation.md` records the sequencing and guardrails.
`TASK-025` remains stretch-only unless the Day 4 checklist is already satisfied.

---

### ADR-021: Report API reads latest successful stored reports while history empty states stay honest

- **Date**: 2026-07-09
- **Status**: Accepted (TASK-039 implementation decision)
- **Decided by**: Backend Implementer

**Context**: PR #29 originally changed `/api/issues/{id}/history` to return an empty `points` array when history was missing or the query failed, but it predated the Day 4 `TASK-039` ledger on `main`. Day 4 `TASK-039` requires `/api/issues/{id}/report` to read latest successful `ai_reports` rows while preserving the accepted `not_yet_generated` empty state.
**Decision**: Preserve the history no-fabrication behavior: live and static fallback history responses return `points: []` when no history is available or the history query fails. Also wire the live report endpoint to the latest successful `ai_reports` row for the issue. Failed report rows are never served; absent reports or report-read failures return the accepted `{"status": "not_yet_generated"}` shape. Static fallback mode keeps its demo-safe sample report.
**Rationale**: Empty history is more honest than plotting a fabricated latest point, and serving only successful stored reports keeps the API read-only and decoupled from report generation. The response shapes stay unchanged, so frontend integration can keep the existing success/empty-state contract.
**Trade-offs**: Static fallback history may show no chart line until richer fallback history is deliberately added. Static fallback report content remains a curated sample, so `TD-009` still needs a Day 5 language/demo fallback note if backend fallback data is used in presentation.
**Consequences**: `TASK-039` is complete for the backend read path. Backend tests now cover latest successful report selection, failed-report exclusion, report-query failure fallback, report unknown-id behavior, and empty history fallback behavior without any schema, dependency, infrastructure, deployment, or public API shape change.

---

### ADR-022: AI provider selection - OpenAI, live call approved for TASK-015 ⚠️ HUMAN APPROVAL

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Data/AI Implementer

**Context**: Technical Design §9 leaves the LLM provider as "Claude or OpenAI."
`reports/day-4-work-allocation.md` (ADR-020) had defaulted `TASK-015`'s
execution to deterministic template generation with any real provider hook
"disabled or stubbed until approved," since calling a paid external AI API is
an `AGENTS.md` Absolute Restriction requiring explicit human approval, and AI
Provider Selection is itself a Human Approval Gate. Before implementation,
the user was asked (1) which provider to select and (2) whether to follow
the Day-4 deterministic default or wire a real live call now. The user chose
OpenAI, then explicitly chose to override the Day-4 default and wire the real
call rather than stub it.
**Decision**: OpenAI is the selected AI provider. `app/core/ai_report.py`
implements `OpenAIReportClient` (real OpenAI Chat Completions call, JSON-mode
response, `response_format={"type": "json_object"}`) behind the `LLMClient`
protocol, constructed explicitly via `build_openai_client()` - never
constructed or called implicitly at import time. `openai==2.44.0` was added
to `backend/requirements.txt` (new dependency, covered by the same user
approval). Settings gained `OPENAI_API_KEY`/`OPENAI_MODEL`
(`app/core/config.py`, `.env.example`) - no key is committed, and no key is
present in this development environment, so no real network call to OpenAI
has actually been made or billed in this session; all tests exercise the
pipeline against a fake `LLMClient`.
**Rationale**: Explicit, repeated human approval was obtained in-session for
both the provider choice and the decision to wire a live call rather than the
deterministic-template default, satisfying both the paid-API and
AI-Provider-Selection approval gates in `AGENTS.md`.
**Trade-offs**: This departs from `reports/day-4-work-allocation.md`'s stated
Day 4 default (deterministic template, no live provider) - that allocation
doc is not being edited to match, since it is PM's dated allocation record;
this ADR is the override of record. Real API cost is now possible the first
time someone runs the batch job with `OPENAI_API_KEY` set, unlike the
deterministic-default path.
**Consequences**: Before any live/demo run of `app/core/ai_report_batch.py`
with a real key, confirm the key is scoped/budgeted appropriately - this ADR
approves the architecture and provider, not an unbounded number of live calls.
2026-07-09 follow-up: the user clarified that the provided `OPENAI_API_KEY`
may be used without asking for separate per-run approval for project-scoped
OpenAI report generation. This standing OpenAI-call approval does not approve
shared/dev database writes, deployments, schema changes, dependency changes, or
public API shape changes; those gates remain separate. `memory/architecture.md`
and `tasks/completed.md` should reference this ADR for TASK-015's provider
choice.

---

### ADR-023: Add psycopg2-binary for provider-copied Postgres URLs

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Debugger

**Context**: The backend already depended on `psycopg[binary]` and documented
`postgresql+psycopg://...` as the preferred SQLAlchemy URL form. Supabase
dashboard connection strings are commonly copied as plain `postgresql://...`.
With that form, SQLAlchemy defaults to the `psycopg2` driver. Local DB
connectivity checks therefore failed with `ModuleNotFoundError: No module named
'psycopg2'` even after the Supabase host and URL parsing were corrected.
**Decision**: Add `psycopg2-binary==2.9.10` to the backend runtime
dependencies while keeping `psycopg[binary]==3.2.3` in place.
**Rationale**: This lets the backend accept provider-copied Supabase
`postgresql://...` URLs without requiring every developer to rewrite the URL
scheme to `postgresql+psycopg://...`. It also keeps the existing psycopg3 path
available for environments that prefer explicit driver selection.
**Trade-offs**: The backend now carries two Postgres drivers. That is a small
dependency increase, but it reduces setup friction during the hackathon.
**Consequences**: `backend/requirements.txt`, `dependencies.md`,
`backend/README.md`, `commands.md`, and `backend/migrations/README.md` document
the supported URL forms and the Supabase direct-host IPv6 fallback path. Live DB
connectivity may still fail on local networks that cannot route Supabase's
direct IPv6 host; use the Supabase pooler connection string in that case.

---

### ADR-024: Apply initial schema to development Supabase DB

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User (human), implementing Debugger

**Context**: After switching `DATABASE_URL` to the Supabase pooler URL,
read-only connectivity succeeded, but live API reads fell back because the
database did not contain application tables such as `market_snapshots`.
`backend/migrations/001_initial_schema.sql` had previously been accepted as
the schema draft but remained unapplied under ADR-011.
**Decision**: With explicit user approval, apply
`backend/migrations/001_initial_schema.sql` to the currently configured
development Supabase database.
**Rationale**: The backend live read path requires the accepted app tables
before it can distinguish "no live rows yet" from "schema missing." Applying
the initial schema unblocks the data seed/collector path while keeping public
API shapes unchanged.
**Trade-offs**: This creates tables in the configured Supabase database. The
tables are currently empty, so user-facing issue routes still serve the
documented static fallback until snapshot/metric data is inserted.
**Consequences**: Expected tables and the `pgcrypto` extension are present in
the development DB. Applying this migration or future schema changes to any
other shared or production database remains approval-gated. The next live-data
step is an approved seed/collector write path, not another schema change.

---

### ADR-025: Local/dev historical seed path for DB-backed charts

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User request, implementing Debugger

**Context**: `ISS-004` was resolved by inserting one live snapshot and metric
row per normalized issue into the configured development DB, which made
`/api/issues` DB-backed. The detail chart still needed older snapshot points:
with only one point per issue, the frontend correctly shows an
insufficient-history state rather than fabricating a trend.
**Decision**: Add `backend/app/core/historical_seed.py` as the approved
local/dev path for demo chart history. It fetches CLOB price-history points for
normalized `price_history_token`s, appends missing timestamps to
`market_snapshots`, inserts a fresh latest `market_metrics` row, runs the
existing expectation-shift detector for those metric rows, and records a
`data_collection_logs` audit row. The CLI refuses to write unless `ENV` is
`local`, `dev`, `development`, or `test`, and
`--confirm-local-dev-write` is present.
**Rationale**: This keeps the chart path live and DB-backed without changing
schema, public API shapes, frontend behavior, or safety policy. It also
preserves the append-only model: existing snapshots/metrics remain untouched,
and repeated runs skip already-present history timestamps.
**Limitations**: Historical CLOB price history supplies chart values, but not
historical volume/liquidity at each point. The seed stores volume/liquidity only
when an inserted point is also the newest known snapshot, and otherwise keeps
those auxiliary fields null; the latest metric still uses the latest available
snapshot plus normalized current activity/liquidity values where needed for the
existing caution calculation.
**Consequences**: Demo prep can now choose between waiting for additional
collector cycles or running the guarded historical seed command documented in
`backend/README.md`. Writing to any shared/prod database remains outside this
approval and must be confirmed separately under `AGENTS.md`.

---

### ADR-026: Combined 24h data and AI report batch

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User request, implementing Data/AI Implementer

**Context**: The implementation had separate modules for snapshot/metric
generation, expectation-shift signal detection, and AI report generation.
As a result, collecting data did not automatically create stored AI summaries,
and there was no checked-in 24h schedule. The user requested four concrete
goals: generate AI summaries for the current DB state, connect data/metric/
signal generation to AI summary generation, run every 24h, and provide a
development-only manual generation path without adding UI.
**Decision**: Add `backend/app/core/scheduled_batch.py` as the combined write
path: normalized/live fetched data -> snapshots/metrics -> signals -> AI
reports -> `data_collection_logs`. Add `--reports-only` for development/demo
AI summary generation against the latest existing metric run. Add
`.github/workflows/daily-batch.yml` to run the combined batch every 24h via
GitHub Actions, with manual `workflow_dispatch` support. Use existing schema,
dependencies, and public API shapes.
**Rationale**: This matches the Technical Design step-8 intent while keeping
the user-facing API read-only and avoiding a UI-only trigger that could be
misread as an end-user action.
**Trade-offs**: The scheduled workflow depends on valid `DATABASE_URL` and
`OPENAI_API_KEY` secrets. If report generation fails, the CLI now exits
non-zero so the workflow surfaces the failure instead of silently producing no
stored summaries.
**Consequences**: The current configured OpenAI key returned `401 Unauthorized`
during the first reports-only run. That run inserted failed `ai_reports` audit
rows but no successful summaries; the report endpoint still returns the
accepted `not_yet_generated` state until the key is corrected and the
reports-only command is rerun.
2026-07-09 follow-up: ADR-027 resolved this by selecting OpenRouter for the
configured key shape; a later reports-only run created successful stored
summaries.

---

### ADR-027: Use OpenRouter key through the OpenAI-compatible SDK path

- **Date**: 2026-07-09
- **Status**: Accepted
- **Decided by**: User request, implementing Data/AI Implementer

**Context**: The current configured AI key is present but OpenAI's default
endpoint rejects it with `401 invalid_api_key`; the provider response indicates
the key shape is OpenRouter-style. The user requested changing the
implementation to use the OpenRouter key.
**Decision**: Keep the existing `openai` Python dependency and
Chat Completions request shape, but support OpenRouter by pointing the OpenAI
SDK at `https://openrouter.ai/api/v1`. `OPENROUTER_API_KEY` is preferred when
present; otherwise an `OPENAI_API_KEY` value with the `sk-or-` prefix selects
OpenRouter automatically. For OpenRouter, unqualified OpenAI model names such
as `gpt-4o-mini` are converted to OpenRouter's `openai/gpt-4o-mini` slug.
**Rationale**: OpenRouter documents OpenAI SDK compatibility through `base_url`,
so this fixes the provider/key mismatch without adding a dependency, changing
schema, or changing the public API. Existing tests can continue using fake
`LLMClient` instances, and the API layer remains read-only.
**Consequences**: Batch report generation can use the existing configured
OpenRouter key without modifying `.env` or printing secrets. Live provider
calls remain explicit batch-side side effects and still pass every generated
summary through the strict schema parser and banned-phrase filter before
storage.

---

### ADR-049: Evidence-completeness contract for grounded v5 reports

- **Date**: 2026-07-11
- **Status**: Accepted and implemented in code; migration remains unapplied
- **Decided by**: User request and Data/AI analysis

**Context**: The live collector preserves the market question but replaces the
source resolution description with generic display copy. The v5 writer can
therefore produce safe metric prose but lacks the condition, exclusions, and
source anchors required for concrete issue-specific scenarios. Requiring three
or four scenarios despite missing definition evidence produces repeated,
low-information output.

**Decision**: Separate `market_definition`, `observed_data`,
`verified_context`, and `data_limitation` evidence. Add provenance-preserving
`resolution_rules`, compute an input-completeness level before generation, and
allow output richness to shrink with evidence availability. The intended public
contract permits one to four scenarios and adds a bounded `basis` enum before
any later claim-level reference expansion. Comparison values, history summaries,
and consistency checks are deterministic backend responsibilities.

**Approval boundary**: This decision fixes the staged design only. TASK-083's
new append-only migration requires explicit database-schema approval before
implementation. TASK-085 and TASK-090 require explicit public API approval.
No development/production database write, deployment, or paid provider call is
authorized by this ADR.

**Consequences**: TASK-082 is complete. TASK-083 is the next task but remains at
its approval gate. The full contract and evaluation matrix are recorded in
`reports/task-082-grounding-contract.md`.

**Implementation follow-up (2026-07-11)**: The user approved the database-schema
and public API code changes. TASK-083~091 completed the append-only schema,
writer/research wiring, completeness-scaled scenarios, exact-title gate,
no-source review, reference values, deterministic history summary, basis
contract, and full integration audit. Migration 003 was not applied to any
database, and no provider call, deployment, or non-test database write occurred.

---

### ADR-051: Positive-first, on-demand issue briefing direction

- **Date**: 2026-07-11
- **Status**: Accepted; TASK-101 implementation active
- **Decided by**: User direction and PM planning

**Context**: Collection-time report generation spends provider budget on
unread issues and couples report failures and prompt revisions to the data
pipeline. V3-v6 progressively added fixed modes, fields, prohibited-language
rules, and quality gates that preserve evidence boundaries but also reject
useful, natural issue briefing prose. The user requested positive-first prompt
instructions, explicit button-triggered generation, broader and simpler
context collection, flexible broad-section output, and historical archival of
superseded contracts before later cleanup.

**Decision**: Separate market collection, external-context collection,
and briefing generation. Let an explicit user request create or join an
idempotent cache-backed generation job. Use a positive-first writer prompt and
a flexible `sections[]` envelope with stable broad categories and evidence
references. Collect context broadly, classify accepted sources by A-D level,
and reserve an independent verifier call for ambiguity, conflict, or high-risk
claims instead of requiring it universally. Keep evidence/shape violations as
blocking checks and treat ordinary prose-quality preferences as diagnostics.

**Historical transition**: Archive v1-v6 contracts with their active dates,
ADRs, and supersession reasons. Preserve stored rows and audit history during
v7 evaluation. Runtime deletion is a separate TASK-109 action after v7 user
acceptance.

**Approval boundary**: On 2026-07-11 the user approved TASK-099 approval items
1-7: v7 AI/wording policy, A-C public source levels, append-only request/lease
schema, on-demand API, scheduled-workflow separation, bounded provider calls,
and append-only local/development writes. Deployment, production writes, new
dependencies, and v1-v6 runtime deletion remain excluded. TASK-109 deletion
requires separate approval after v7 acceptance.

**Consequences**: TASK-100~108 proceed in dependency order under the approved
boundary. TASK-109 may audit and propose cleanup but cannot delete legacy
runtime until the separate acceptance and deletion gate is satisfied.

---

### ADR-052: Preserve last-good content across v7 request states

- **Date**: 2026-07-11
- **Status**: Accepted and implemented in TASK-106
- **Decided by**: Frontend implementation of the approved ADR-051 API contract

**Context**: The v7 report API may return a minimal request state when no valid
report exists or a full report carrying a newer generating/failed request. A
single loading replacement would unnecessarily hide already validated content.

**Decision**: Mirror the public API state directly. Minimal idle, generating,
and failed responses render state-only panels. Full generating and
failed-with-last-good responses keep the valid report visible with an explicit
status notice. Stale and failed-with-last-good results offer the same
idempotent generate/join action. Internal source excerpts remain validation
data; the public source card shows only source metadata and supported claims.

**Consequences**: Core issue data never waits for briefing generation. Every
briefing state keeps data-as-of and caution visible. TASK-107 must verify the
polling, last-good, cache, evidence, copy, and failure boundaries. TASK-109
legacy deletion remains separately approval-gated.
