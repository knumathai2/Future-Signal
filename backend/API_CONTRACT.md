# API Contract — Outlook Signals

_Status: Implemented strict v4 runtime contract as defined by ADR-038 and
ADR-043. TASK-062 validates stored metric, episode, verified-candidate,
citation-source, and timing integrity before serving a report.
The runtime shapes are backed by Pydantic schemas
(`app/schemas/issues.py`, `app/schemas/health.py`) and routes
(`app/api/routes/`). Legacy v1 and v2 report contents are gated out
and treated as not yet generated._

**All endpoints are read-only.** All timestamps are ISO 8601 UTC. Public
paths use `issues` / `signals` / `reports` / `categories` — never `markets`,
`bets`, `trades`, `positions`, or `profits` (enforced by
`tests/test_issues_contract.py::test_public_paths_never_use_market_terminal_vocabulary`).

**Current implementation state** (TASK-010/TASK-062): issue and history routes
read from Postgres via `app/db/session.py::get_db()` when `DATABASE_URL` is
set and live `market_snapshots` data exists. The report route reads the latest
successful stored `prompt_version="v4"` evidence bundle in live mode and
otherwise preserves the accepted empty state. Static fallback data never
fabricates a v4 report. Migration `002_context_candidates.sql` remains
unapplied pending the separately guarded TASK-065 local/development run; no
production database write is approved.

## `GET /api/health`

No params. See `app/schemas/health.py::HealthResponse`.

```json
{ "status": "ok", "service": "outlook-signals-api", "time": "2026-07-08T09:00:00Z" }
```

## `GET /api/issues`

Ranked/browsable issue list.

| Param | Type | Default | Notes |
|---|---|---|---|
| `category` | string | none | match against `/api/categories` broad Korean filter values; raw stored category values are also accepted for backward compatibility |
| `window` | enum `24h`\|`7d` | `24h` | which change field ranking/`sort=change` uses |
| `sort` | enum `heat`\|`change`\|`recent` | `heat` | |
| `limit` | int 1-100 | 20 | |
| `offset` | int ≥0 | 0 | |

```json
{
  "data_as_of": "2026-07-08T09:00:00Z",
  "issues": [
    {
      "id": "b3f1c2a4-0000-4000-8000-000000000001",
      "title": "Will the proposed climate accord be ratified by December 2026?",
      "category": "environment",
      "current_value": 0.63,
      "change_24h": 0.082,
      "change_7d": 0.11,
      "confidence_level": "sufficient",
      "heat_score": 78.4
    }
  ]
}
```

## `GET /api/issues/{id}`

Full issue detail, including embedded related-event candidates and signals
(Technical Design §5 notes both can be folded into detail for MVP instead of
separate calls — done here).

```json
{
  "id": "b3f1c2a4-0000-4000-8000-000000000001",
  "title": "Will the proposed climate accord be ratified by December 2026?",
  "description": "Tracks reflected expectation on ratification of the multilateral climate accord.",
  "category": "environment",
  "status": "active",
  "outcome_label": "Yes",
  "current_value": 0.63,
  "change_24h": 0.082,
  "change_7d": 0.11,
  "confidence_level": "sufficient",
  "heat_score": 78.4,
  "data_as_of": "2026-07-08T09:00:00Z",
  "related_events": [
    { "event_title": "...", "event_date": "2026-07-01T00:00:00Z", "note": "A related event candidate, not a cause: ..." }
  ],
  "signals": [
    { "signal_type": "expectation_shift", "severity": "medium", "window": "24h", "magnitude": 0.082, "triggered_at": "2026-07-08T09:00:00Z" }
  ]
}
```

`404` if `id` is unknown.

## `GET /api/issues/{id}/history?window=24h|7d|30d`

```json
{
  "data_as_of": "2026-07-08T09:00:00Z",
  "window": "7d",
  "points": [{ "captured_at": "2026-07-08T09:00:00Z", "value": 0.63 }]
}
```

`404` if `id` is unknown.

## Historical v3 report runtime — no longer served

Before TASK-062, the latest AI report used fixed v3 template slots
(ADR-003, updated by ADR-033) — and must pass the banned-phrase filter before
storage.
Rows using prompt versions v1 through v3 remain append-only audit history but
are never returned by the current endpoint. The example below is retained only
as historical contract documentation.

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "status": "success",
  "report_version": "v3",
  "generated_at": "2026-07-10T09:05:00Z",
  "data_as_of": "2026-07-10T09:00:00Z",
  "content": {
    "issue_overview": "이 이슈는 공개된 기한까지 문서에 적힌 조건이 충족되는지를 추적합니다.",
    "current_data_reading": "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며, 24시간 전보다 8.2퍼센트포인트 높게 관찰되었습니다.",
    "possible_outlook": "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, 이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다.",
    "possible_drivers": "이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다. 현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해 독립적으로 확인해야 합니다.",
    "external_context": null,
    "what_to_check": "게시된 이슈 문구와 기록된 기한, 데이터 기준 시각, 이후 공개 데이터 갱신 내용을 추가로 확인해야 합니다.",
    "data_limitations": "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 7일 이력 범위의 영향을 받습니다. 공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다.",
    "caution_note": "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, 다른 자료를 통해 독립적으로 확인해야 합니다."
  }
}
```

If no report exists yet:

```json
{ "status": "not_yet_generated" }
```

`404` if `id` is unknown.

Per ADR-008, this returns `200` with `{"status": "not_yet_generated"}`
rather than Technical Design §5's originally proposed `204` (HTTP `204 No
Content` cannot carry a body per spec, so most clients would discard the
hint). This is accepted as final, not an open item.

## `GET /api/issues/{id}/report` — current strict v4 runtime

The path remains `GET /api/issues/{id}/report`; no new public endpoint was
added. The endpoint serves only the latest
successful `prompt_version="v4"` row whose seven-field content, metric
evidence, verified candidates, stored citation sources, episode linkage, and
timing all validate. Legacy v1-v3, failed, malformed, withheld/rejected,
unknown-evidence, source-mismatched, and `data_as_of > generated_at` rows are
treated as `not_yet_generated`.

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "status": "success",
  "report_version": "v4",
  "generated_at": "2026-07-11T09:05:00Z",
  "data_as_of": "2026-07-11T09:00:00Z",
  "episode_at": "2026-07-11T08:00:00Z",
  "content": {
    "issue_overview": "...",
    "observed_change": "...",
    "context_summary": null,
    "relationship_boundary": "...",
    "what_to_check": "...",
    "data_limitations": "...",
    "caution_note": "..."
  },
  "evidence_refs": ["metric:123"],
  "context_candidates": []
}
```

`content` has exactly the seven keys above. Only `context_summary` is nullable;
all other keys are required non-empty strings. If it is non-null, at least one
`candidate:<uuid>` must appear in `evidence_refs`, resolve to the same market
and compatible episode, have `verification_state="verified"`, and have at
least one stored public citation source. Every metric sentence must be
supported by a `metric:<id>` reference and match its stored values.

A public context candidate has exactly this shape:

```json
{
  "id": "8b441a56-0000-4000-8000-0000000000bb",
  "title": "...",
  "event_at": "2026-07-11T07:30:00Z",
  "summary": "...",
  "sources": [
    {
      "title": "...",
      "url": "https://example.gov/source",
      "domain": "example.gov",
      "published_at": "2026-07-11T07:00:00Z",
      "source_type": "official"
    }
  ]
}
```

`source_type` is `official` or `independent_secondary`; `published_at` alone
may be null. URL/title/domain values must equal stored values derived from
OpenRouter API `url_citation` annotations. Internal verification scores,
source excerpts, model output, query text, usage cost, withheld/rejected
candidates, and secrets are never returned.

When no verified candidate exists, `context_summary` is JSON `null`,
`context_candidates` is an empty array, and `evidence_refs` contains metric
references only. The API does not generate a candidate-absence sentence.
Unknown issue remains `404`; missing valid v4 content remains the accepted
`200 {"status":"not_yet_generated"}` response.

The read path reconstructs the deterministic v4 fields from the linked metric,
latest snapshot at or before that metric, and the exact same-episode verified
candidate rows. It rejects a bundle if reconstructed content differs, if the
metric or candidate reference list is missing/reordered/unknown, if a candidate
is not verified, if its episode differs, if its source list is empty or fails
the strict stored citation schema, or if `data_as_of`/`episode_at` is later than
`generated_at`. Source URL hostname and public `domain` must also match. The
API returns no internal citation ID, canonical URL, content hash, verification
score, query, excerpt, model output, or provider-usage field.

## Legacy v2 report contract (Superseded by v3)

The legacy v2 report shape is no longer served from the API. The existing generator may still generate v2 reports internally until TASK-049 is resolved, but the public API filters these out as `not_yet_generated`.

## Approved v3 report contract replacement (TASK-048, ADR-033)

This section remains as the historical contract design freeze. ADR-033 supersedes ADR-032.

The approved `content` object has exactly these eight keys:

```json
{
  "issue_overview": "...",
  "current_data_reading": "...",
  "possible_outlook": "...",
  "possible_drivers": "...",
  "external_context": "...",
  "what_to_check": "...",
  "data_limitations": "...",
  "caution_note": "..."
}
```

### Differences from the current v2 runtime and ADR-032

- The current v2 runtime has eight fields but uses the issue-explainer and
  three-scenario shape shown above in the current contract.
- ADR-032 accepted an eleven-field `content` object with a nullable
  `context_candidate_note`, three separate scenario fields, and separate
  `current_reading` and `recent_change_summary` fields.
- ADR-033 consolidates ADR-032 into eight content fields, introduces
  `possible_drivers`, and makes `external_context` the only nullable value.
- `possible_outlook` can be misread as a real-world forecast. The approved
  contract limits it to conditional descriptions of how the public-data
  reading could continue, expand, or moderate; it cannot state a result, a
  result probability, or a future direction as fact.
- `possible_drivers` can be misread as causal analysis. The approved contract
  permits only manually reviewed or structured-input factor candidates and
  requires an adjacent statement that the available data does not establish
  influence or causation. Its frontend label avoids causal wording.
- The two risky key names remain in the frozen contract under the approved
  non-forecasting and non-causal validation rules. Their Frontend labels remain
  the safer display boundary defined below.

### ADR-032 field mapping

| ADR-032 content field | Approved v3 field | Change | Boundary preserved by ADR-033 |
|---|---|---|---|
| `issue_explainer` | `issue_overview` | Renamed and narrowed | Explain the issue and its resolution condition; do not add unsupported significance claims. |
| `why_it_matters` | `issue_overview` | Standalone field removed; source-backed orientation may be consolidated | Keep only context needed to understand the issue; do not speculate about impact. |
| `current_reading` | `current_data_reading` | Consolidated | Describe the current reflected expectation value only as a public-data reading. |
| `recent_change_summary` | `current_data_reading` | Consolidated | Include observed window, direction, magnitude, and timing when available. |
| `context_candidate_note` | `external_context` | Renamed; remains nullable | Use manually reviewed context only and keep source metadata outside the narrative. |
| `scenario_major_change` | `possible_outlook` | Consolidated | Conditional development only; no future-result assertion. |
| `scenario_limited_change` | `possible_outlook` | Consolidated | Conditional development only; no future-result assertion. |
| `scenario_status_quo` | `possible_outlook` | Consolidated | Conditional development only; no future-result assertion. |
| `check_points` | `what_to_check` | Renamed | List verification items, not actions on an outcome. |
| `data_limitations` | `data_limitations` | Retained | State activity, volatility, history, and representativeness limits. |
| `caution_note` | `caution_note` | Retained | Mandatory report-level interpretation caution for every successful report. |
| No ADR-032 equivalent | `possible_drivers` | New field | Factor candidates to check alongside movement; never a causal explanation. |

### Successful response and top-level fields

For a successful v3 report, the endpoint would keep the existing path and
return the following top-level fields. Timestamps are timezone-aware ISO 8601
UTC values. `data_as_of` must be less than or equal to `generated_at`.

| Field | v3 behavior |
|---|---|
| `id` | Required UUID string for a successful stored report. |
| `status` | Required literal `success`. |
| `report_version` | Required literal `v3`, derived from the accepted prompt/schema version. |
| `generated_at` | Required report-generation timestamp from the stored row. |
| `data_as_of` | Required timestamp derived through `input_metrics_id` to `market_metrics.computed_at`; it is never generated text. |
| `content` | Required object that contains every approved key exactly once; no extra or missing key is accepted. |

Complete approved example:

```json
{
  "id": "7c2e1a90-0000-4000-8000-0000000000aa",
  "status": "success",
  "report_version": "v3",
  "generated_at": "2026-07-10T09:05:00Z",
  "data_as_of": "2026-07-10T09:00:00Z",
  "content": {
    "issue_overview": "이 이슈는 공개된 기한까지 문서에 적힌 조건이 충족되는지를 추적합니다.",
    "current_data_reading": "데이터 기준 시각에 공개 예측시장 참여자 데이터에 반영된 기대값은 63%이며, 24시간 전보다 8.2퍼센트포인트 높게 관찰되었습니다.",
    "possible_outlook": "이후 공개 데이터에서 관찰된 움직임의 지속, 확대 또는 완화가 확인되더라도, 이는 데이터의 흐름만 설명하며 현실의 결과나 변화의 이유를 입증하지 않습니다.",
    "possible_drivers": "이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다. 현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해 독립적으로 확인해야 합니다.",
    "external_context": null,
    "what_to_check": "게시된 이슈 문구와 기록된 기한, 데이터 기준 시각, 이후 공개 데이터 갱신 내용을 추가로 확인해야 합니다.",
    "data_limitations": "이 읽기는 활동량, 유동성, 24시간 변화 폭, 24시간 및 7일 이력 범위의 영향을 받습니다. 공개 예측시장 참여자 데이터는 전체 대중의 판단을 대표하지 않습니다.",
    "caution_note": "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, 다른 자료를 통해 독립적으로 확인해야 합니다."
  }
}
```

The successful response always includes both `data_as_of` and the non-empty
`content.caution_note`. A report that cannot satisfy either requirement is not
served as a successful v3 report.

### Exact v3 content decision table

Length is measured as the number of Unicode code points after trimming leading
and trailing whitespace. Backend enforcement uses Python `len()` after
Pydantic string trimming. A future Frontend implementation must use
`Array.from(value.trim()).length`, not JavaScript UTF-16 `string.length`, if it
performs the same validation. Length is not measured in bytes, grapheme
clusters, or model tokens.

| Field name | Purpose | Input source or producer | API type | Required or nullable | Minimum length | Maximum length | Length measurement unit | Frontend label | Display order | Safety validation | Missing-value behavior |
|---|---|---|---|---|---:|---:|---|---|---:|---|---|
| `issue_overview` | Explain what the issue is and the documented condition being tracked. | Stored title, description, category, tracked outcome label, and optional end date. The later generator input must expose only the values that exist. | string | Required, non-null | 30 | 600 | Trimmed Unicode code points | Issue Overview | 1 | No outcome assertion, unsupported significance claim, or broader-public claim. | If title and description do not document the tracked condition clearly enough, reject the report; do not invent resolution criteria. |
| `current_data_reading` | Describe the values and movement currently observed in public data. | Current snapshot, fixed 24h/7d computed changes, inflection timing, and `data_as_of`; deterministic values phrased by the Data/AI template. | string | Required, non-null | 50 | 700 | Trimmed Unicode code points | Current Data Reading | 2 | Must identify the reading as public participant data; no real-world probability or unsupported metric. | If a fixed comparison window is unavailable, state that limitation and omit its magnitude. If no current snapshot exists, reject the report. |
| `possible_outlook` | Describe conditional developments in later public-data readings without forecasting a real-world outcome. | Current reading and fixed 24h/7d changes; fixed Data/AI template only. It does not use an external event to explain later movement. | string | Required, non-null | 60 | 700 | Trimmed Unicode code points | Conditional Developments | 5 | Conditional data-reading language only; no result probability, certainty, asserted future direction, or external-condition linkage. | Use the fixed later-reading pattern defined below. If no current snapshot exists, reject the report. |
| `possible_drivers` | Identify reviewed context candidates that can be compared with movement without asserting a relationship. | Title and date from PM/Data-approved curated `related_events` rows; deterministic template only. | string | Required, non-null | 80 | 700 | Trimmed Unicode code points | Factors to Check Alongside the Movement | 4 | Must state that timing is for comparison and that no relationship is established; causal connectors and rankings are blocked. | If no approved candidate exists, use the fixed no-candidate statement defined below; do not invent a factor. |
| `external_context` | Present the approved narrative note for manually reviewed external context. | `related_events[].note` from the PM/Data-approved curated path; no new inference or provenance claim may be added. | string or null | Key required; value nullable | 40 when non-null | 700 when non-null | Trimmed Unicode code points | External Context | 3 | Every context item must be manually reviewed and carry candidate-not-cause wording; no automatically matched material. | Use `null` when approval cannot be established or no reviewed note exists. Empty string and placeholder copy are rejected; Frontend hides the section only for `null`. |
| `what_to_check` | List documented text, dates, and data updates requiring further verification. | Stored title/description, optional end date, approved context title/date, structured missing-input flags, and `data_as_of`. | string | Required, non-null | 30 | 600 | Trimmed Unicode code points | What to Check | 6 | Verification language only; no instruction to act on an outcome and no unsupported source or official-status claim. | If issue-specific items are unavailable, require a fixed check of the published issue wording, recorded dates, later public-data updates, and timestamp. |
| `data_limitations` | Explain limitations involving activity, liquidity, the current large-movement volatility proxy, history, and representativeness. | Fixed 24h/7d changes, snapshot volume/liquidity inputs, history availability, caution enum, and source-scope constants. A later prompt-input extension is required. | string | Required, non-null | 80 | 700 | Trimmed Unicode code points | Data Limitations | 7 | Must describe every independently detected limitation, even when enum precedence exposes only one level, and must not claim broader-public representativeness. | Missing comparison inputs force the `insufficient_data` limitations template; the section is never hidden. |
| `caution_note` | Provide the mandatory interpretation-caution statement for the report as a whole. | Exact deterministic Korean template selected from `confidence_level`, then equality/clause and safety validated. | string | Required, non-null | 120 | 700 | Trimmed Unicode code points | Interpretation Caution | 8 | Must include public-participant scope, no real-world-result claim, broader-public limitation, and independent verification. | If the caution enum is missing or the exact required copy cannot be rendered, reject the report; the section is never hidden. |

Fixed Korean no-candidate statement for `possible_drivers`:

> 이 움직임과 함께 비교할 수 있도록 수동 검토를 마친 맥락 후보가 없습니다.
> 현재 데이터는 관찰된 움직임만 보여 주며, 추가 맥락은 다른 자료를 통해
> 독립적으로 확인해야 합니다.

### Input availability and provenance

The later implementation must not assume that every conceptual input already
exists in `ReportPromptInputs`.

| Input | Current availability | v3 contract use |
|---|---|---|
| Title, description, category | Stored and already passed to the generator. | `issue_overview`, with no added resolution claim. |
| Tracked outcome label and optional end date | Stored, but not currently passed to `ReportPromptInputs`. | May be added to the later prompt-input object without a database change. |
| Distinct resolution criteria | No dedicated stored field. The title or description may contain relevant wording. | Do not claim a criterion beyond the stored text. Richer criteria require a separate approved input-pipeline decision. |
| Current value, 24h change, 7d change, caution enum, inflection summary | Stored/computed and already passed. The generation windows are fixed at 24h and 7d; there is no persisted user-selected report window. | `current_data_reading`, `possible_outlook`, `data_limitations`, and `caution_note`. |
| Snapshot activity and liquidity values | Stored on snapshots but not currently passed to `ReportPromptInputs`. | A later prompt-input extension must expose the report-snapshot values or precomputed limitation flags so `data_limitations` can report all detected limits. |
| Related-event title, optional date, and note | Stored for the manually curated demo path. The current generator concatenates only its first match. | A later deterministic loader must keep title/date for `possible_drivers` and approved note text for `external_context` instead of duplicating one combined sentence. |
| Source URL, source type, review-status flag, participant breadth | Not stored or passed. | Not available to v3. Do not imply these exist. URL or structured review metadata requires separate approval and may require a schema/API change. |

The report generator remains Korean. The complete example, no-candidate
literal, and caution matrix therefore use Korean fixtures. Each fixture must
pass the same trimmed Unicode-code-point bounds as generated content. Every
generated narrative field remains limited to 1-5 concise sentences. The
approved maximums are an upper bound, not a target for every response.

### `external_context` representation decision

| Option | Compatible with the fixed eight-field contract? | Metadata and review implications | Decision |
|---|---|---|---|
| A. Narrative text in `external_context`; metadata elsewhere | Yes. The field remains `string | null`, and existing issue-detail `related_events` remains the metadata area. | Current metadata is title, reviewed note, and an event date when recorded. A source URL is not present in the current DB or public response. Every included item must be manually reviewed. | **Selected by ADR-033.** |
| B. Structured narrative plus source metadata object | Not compatible with the approved string type. It could stay within eight keys only by changing this field to an object. | Better association of title/date/URL, but URL is not currently stored. Changing the type requires separate public API approval and coordinated Backend/Frontend/Data work. Adding metadata outside `content` would be an additional public API field and also requires approval. | Not selected. |
| C. Source information embedded in the narrative string | Technically compatible. | Metadata becomes difficult to validate, parse, link, and update; URLs would consume narrative length and mix provenance with generated copy. | Rejected. |

Under Option A:

- `external_context` includes only PM/Data-reviewed narrative derived from
  manually curated related-event candidates.
- The existing `GET /api/issues/{id}` `related_events` array remains the only
  public metadata area. It currently exposes title, note, and a date when
  recorded, but no URL.
- Every context item must be manually reviewed before it can be used. Automated
  news collection, matching, scoring, display, and database insertion remain
  out of scope.
- Manual review is an operational invariant, not a stored boolean in the
  current schema. Data/AI may consume only records from the PM/Data-approved
  curated path. If that approval cannot be established, `external_context`
  must be `null` and `possible_drivers` must use the fixed absence statement.
- An issue without manually reviewed context uses JSON `null`. It does not use
  an empty string or fixed explanatory copy, and the Frontend hides only that
  section.
- If the report response itself must later carry structured source metadata,
  that is a separate public API change. It requires PM/user approval and, if a
  URL is to be persisted, a separately approved storage/schema decision.

### Weak-inference rules for `possible_drivers`

The field is a deterministic candidate index, not a narrative explanation. It
may name only the approved candidate title and recorded date, and it must state
that the timing is offered for comparison without establishing a relationship.
The corresponding approved narrative note belongs only in `external_context`.
The field cannot infer new external facts, rank candidates, or turn a reviewed
event into an explanation of the movement.

Allowed patterns:

- "A manually reviewed context candidate dated [date] can be compared with the
  timing of the observed movement."
- "The recorded timing is provided only for comparison."
- "The available data does not establish a relationship between this
  candidate and the movement."

Blocked patterns:

- Causal connectors that link a candidate to movement, including formulations
  equivalent to "because", "due to", "caused by", "led to", or "resulted in".
- Claims that a candidate explains, drove, triggered, or produced the movement.
- Ranked or confident candidate language such as "main factor", "primary
  explanation", or numeric confidence in influence.
- Any factor not present in structured inputs or a PM/Data-approved manual
  context candidate.

Korean generated text must also block causal-link patterns such as `때문에`,
`~로 인해`, `원인`, `주요 요인`, `영향을 주었다`, `촉발했다`, or a claim
that the candidate `설명한다` the movement. These strings are quoted here only
to define validation rules.

The key name `possible_drivers` itself can imply causal analysis. ADR-033
retains it only with the public label "Factors to Check Alongside the
Movement" and the semantic validator rules above.

### Safety rules for `possible_outlook`

Allowed content is limited to:

- Conditional descriptions of what a later public-data reading might show.
- Neutral descriptions of the observed movement continuing, expanding, or
  moderating.
- Items whose confirmation requires independent verification.

Allowed patterns:

- "If later public-data readings show continuation, expansion, or moderation,
  that would describe only the dataset."
- "Such a reading would not establish a real-world result or explain why the
  movement occurred."
- "Any later reading requires independent verification."

Blocked patterns:

- Statements that a real-world result will or will not occur.
- Numeric or qualitative claims about the probability of a real-world result.
- Assertions that the reflected value will rise, fall, reverse, or continue.
- Labels such as a preferred, favorable, adverse, or expected scenario.
- Any action-oriented conclusion or wording that presents the section as an AI
  forecast.

Korean generated text must also block certainty/forecast patterns such as
`~할 것이다`, `~하게 된다`, `가능성이 높다`, `가능성이 낮다`, `상승이
이어진다`, `하락이 이어진다`, `전망`, or `예측` when they characterize a
real-world result or assert a future data direction. These strings are quoted
here only to define validation rules.

The key name `possible_outlook` can itself be read as forecasting. ADR-033
retains it only with the Frontend label "Conditional Developments" and the
field-level restrictions above.

### Mandatory `caution_note` copy by caution level

The phrase "low caution level" is not used in this contract. `sufficient`
means that the current data meets the configured sufficiency thresholds; it
does not mean that no caution is needed. `caution_low_activity` specifically
means that recent activity is limited.

Every enum value must communicate all four baseline meanings:

1. The reading comes from public participant data.
2. It does not represent the broader public.
3. It does not establish a real-world outcome.
4. The reader should verify the information independently.

| `confidence_level` enum | Meanings that must appear | Condition-specific limitation | Approved deterministic Korean literal | Additional blocked wording patterns |
|---|---|---|---|---|
| `sufficient` | All four baseline meanings; 24h and 7d comparisons exist, activity and liquidity are not below their configured floors, and absolute 24h movement does not exceed the configured large-movement threshold. | Sufficiency applies only to the available inputs, not accuracy, representativeness, or outcome certainty. | "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 24시간 및 7일 비교 지점이 있고 활동량과 유동성이 설정된 하한보다 낮지 않으며 24시간 변화 폭이 큰 움직임 기준을 넘지 않지만, 다른 자료를 통해 독립적으로 확인해야 합니다." | "No caution needed", "fully reliable", "confirms the outcome", or any equivalent assurance. |
| `caution_low_activity` | All four baseline meanings; reported 24h volume or liquidity is unavailable or below its configured floor. | Movement may be more sensitive to limited activity or available depth. The enum does not establish observation count, staleness, or participant identity. | "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 24시간 활동량 또는 유동성이 없거나 설정된 하한보다 낮아 관찰된 변화가 제한된 활동이나 깊이에 민감할 수 있으므로, 다른 자료를 통해 독립적으로 확인해야 합니다." | Claims that the movement is invalid, can be ignored, is stale, or was caused by a particular participant. |
| `caution_high_volatility` | All four baseline meanings; history and low-activity gates passed, then absolute 24h movement exceeded 15pp. | This is a large 24-hour-movement proxy, not evidence of repeated variation and not a real-world result. | "이 내용은 공개 예측시장 참여자 데이터에 나타난 흐름을 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 필요한 비교 지점과 활동 조건을 통과했지만 24시간 기대값 변화의 절대 폭이 15퍼센트포인트를 넘어 단기 움직임을 안정된 흐름으로 해석하기 어려우므로, 다른 자료를 통해 독립적으로 확인해야 합니다." | Claims that the movement will continue, will reverse, proves instability, or predicts the real-world result. |
| `insufficient_data` | All four baseline meanings; at least one required 24h or 7d comparison point is unavailable. | Direction, magnitude, continuity, or comparison-window statements must be omitted when unsupported. | "이 내용은 제한된 공개 예측시장 참여자 데이터를 정리한 것이며, 전체 대중의 판단을 대표하거나 현실의 결과를 입증하지 않습니다. 필요한 24시간 또는 7일 비교 지점 중 하나 이상이 없어 요청 구간의 방향, 크기, 연속성을 판단할 수 없으므로, 다른 자료를 통해 독립적으로 확인해야 합니다." | Fabricated comparison values, implied continuity, "no change occurred", or any outcome conclusion drawn from missing data. |

The current enum precedence is `insufficient_data` first, then
`caution_low_activity`, then `caution_high_volatility`, then `sufficient`.
Because one enum can hide another raw limitation, `data_limitations` must use
the report-snapshot inputs to state every independently detected limitation;
it must not rely on the enum alone.

For the Korean runtime path, `caution_note` is selected deterministically from
the four literals above. Validation must require exact equality to the selected
literal or verify every required clause after an approved copy revision. A
length check and prohibited-term scan alone do not prove that the four baseline
meanings are present.

All copy must also pass the project-wide English/Korean hard-block term scan,
future-outcome, causal-claim, certainty, action-advice, and participant-following
pattern checks in `standards.md`, `memory/glossary.md`, and ADR-033. The matrix
adds condition-specific requirements; it does not weaken the shared policy.

### Approved Frontend section order and labels

This mapping is the approved contract documentation only. It must not be
connected to the runtime UI until Backend, Data/AI, and Frontend switch
together in coordinated implementation tasks.

The display order is evidence-first: reviewed external context appears before
candidate comparison and conditional-development copy. The JSON object itself
has no semantic key order.

```ts
type V3IssueReportContent = {
  issue_overview: string;
  current_data_reading: string;
  possible_outlook: string;
  possible_drivers: string;
  external_context: string | null;
  what_to_check: string;
  data_limitations: string;
  caution_note: string;
};

type V3ReportSection = {
  key: keyof V3IssueReportContent;
  label: string;
};

const V3_REPORT_SECTIONS = [
  { key: "issue_overview", label: "Issue Overview" },
  { key: "current_data_reading", label: "Current Data Reading" },
  { key: "external_context", label: "External Context" },
  {
    key: "possible_drivers",
    label: "Factors to Check Alongside the Movement",
  },
  { key: "possible_outlook", label: "Conditional Developments" },
  { key: "what_to_check", label: "What to Check" },
  { key: "data_limitations", label: "Data Limitations" },
  { key: "caution_note", label: "Interpretation Caution" },
] as const satisfies readonly V3ReportSection[];
```

The English labels are semantic contract references, not final shipped locale
copy. Approved Korean labels for the current UI are:

| Key | Approved Korean label |
|---|---|
| `issue_overview` | 이슈 개요 |
| `current_data_reading` | 현재 데이터 읽기 |
| `external_context` | 외부 맥락 |
| `possible_drivers` | 변화와 함께 확인할 요인 |
| `possible_outlook` | 조건부 전개 |
| `what_to_check` | 추가 확인 사항 |
| `data_limitations` | 데이터 한계 |
| `caution_note` | 해석 주의 |

Both label sets describe reading, context, verification, and caution rather
than an outcome or action, so ADR-033 accepts them as the implementation
contract copy.

`external_context` is the only nullable value. Its heading and body are both
hidden exactly when the API value is `null`:

```tsx
if (
  section.key === "external_context" &&
  content.external_context === null
) {
  return null;
}
```

No section is hidden for an empty string because empty and whitespace-only
strings are invalid. A later Frontend test must assert eight unique mapping
keys and exact set equality with the frozen content type/schema; `satisfies`
alone checks key validity but not exhaustiveness.

ADR-033 does not add top-level `confidence_level`. Therefore the stored
report's `caution_note`, not the current issue object's caution badge, is the
snapshot-bound caution indicator. A later UI must not present a current issue
badge as if it qualifies a stored report when their `data_as_of` values differ.
On mobile and desktop, render a compact fixed report-caution strip and the
report's `data_as_of` directly adjacent to `current_data_reading`, while keeping
the full `caution_note` at the end. Labels must wrap naturally without ellipsis
or truncation. The later Frontend task must verify the maximum-length fixtures
at 320px and 375px widths before release. If a snapshot-bound enum badge is
required instead, adding `confidence_level` to the report response would
require a future separate public API approval.

### Implementation-draft Pydantic v2 model for v3 `ReportContent`

This snippet is not applied to `app/schemas/issues.py` in TASK-048. It shows
the proposed structural validation for a later coordinated implementation.

```python
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportContent(BaseModel):
    """Draft v3 fixed-slot report content; semantic safety runs before storage."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    issue_overview: Annotated[
        str,
        Field(
            strict=True,
            min_length=30,
            max_length=600,
            description="What the issue is and the condition being tracked.",
        ),
    ]
    current_data_reading: Annotated[
        str,
        Field(
            strict=True,
            min_length=50,
            max_length=700,
            description="Values and movement currently observed in public data.",
        ),
    ]
    possible_outlook: Annotated[
        str,
        Field(
            strict=True,
            min_length=60,
            max_length=700,
            description="Conditional developments without a real-world forecast.",
        ),
    ]
    possible_drivers: Annotated[
        str,
        Field(
            strict=True,
            min_length=80,
            max_length=700,
            description="Reviewed context candidates to compare without causation.",
        ),
    ]
    external_context: Optional[
        Annotated[
            str,
            Field(
                strict=True,
                min_length=40,
                max_length=700,
                description="Manually reviewed external context narrative.",
            ),
        ]
    ]
    what_to_check: Annotated[
        str,
        Field(
            strict=True,
            min_length=30,
            max_length=600,
            description="Facts, dates, criteria, and sources needing verification.",
        ),
    ]
    data_limitations: Annotated[
        str,
        Field(
            strict=True,
            min_length=80,
            max_length=700,
            description="Activity, volatility, history, and representativeness limits.",
        ),
    ]
    caution_note: Annotated[
        str,
        Field(
            strict=True,
            min_length=120,
            max_length=700,
            description="Mandatory report-level interpretation caution.",
        ),
    ]
```

`external_context` intentionally has no default, so the key is required even
though its value may be `null`. Every other field is required and non-null.
`str_strip_whitespace=True` removes leading and trailing whitespace before
length checks; empty and whitespace-only strings then fail `min_length`.
`strict=True` rejects non-string values, and `extra="forbid"` rejects extra
keys. Because no field has a default, missing keys are rejected. The later
Data/AI implementation must additionally run the semantic safety rules above
before storage; structural Pydantic validation alone is not sufficient.

### Legacy behavior, compatibility, and implementation boundary

- Legacy v1 and v2 rows remain append-only audit history.
- A later v3 read path may serve only successful rows whose prompt/schema
  version is `v3` and whose content validates against the frozen v3 schema.
- If only v1/v2, failed, malformed, or otherwise incompatible rows exist, the
  endpoint continues to return `200` with
  `{"status": "not_yet_generated"}`.
- Unknown issue IDs continue to return `404`.
- No current response is partially transformed from v1/v2 to this contract.
- This contract uses the existing `/api/issues/{id}/report` endpoint and existing
  JSONB report storage. It requires no database migration and adds no endpoint.
- TASK-048 does not change runtime Pydantic schemas, generator prompts,
  validators, API routes, tests, frontend types, UI mapping, database rows,
  dependencies, infrastructure, or deployment.

### Contract-freeze approval resolution

ADR-033 records PM/user approval of:

1. The eight-field replacement for ADR-032, without editing ADR-032's history.
2. Retaining `possible_outlook` and `possible_drivers` with the approved
   non-forecasting and non-causal validation rules.
3. Option A for `external_context`, including `string | null`, hide on `null`,
   and source metadata remaining in issue-detail `related_events`.
4. Trimmed Unicode-code-point bounds with the approved maximums above and a
   per-field limit of 1-5 sentences. Frontend must use the same counting rule
   if it validates content.
5. The mandatory caution-copy matrix, enum semantics, precedence, and
   deterministic Korean literals.
6. Keeping top-level `confidence_level` out of the report response and treating
   `caution_note` as the report-snapshot caution indicator.
7. The evidence-first Frontend order and English/Korean label mapping, subject
   to 320px and 375px fixture QA before runtime release.
8. The exact provenance boundary: fixed 24h/7d windows, no distinct
   resolution-criteria field, no source URL or review flag, and only
   no-migration prompt-input extensions for already stored values.

Backend, Data/AI, and Frontend runtime changes remain separate coordinated
implementation tasks. This approval does not itself switch any runtime path.

## `GET /api/categories`

When live issue data is available, this returns broad Korean filter categories
for currently servable issues, such as `정치`, `경제`, `기술`, `세계`, and
`스포츠`. More specific labels such as `우크라이나 전쟁` or `이란 전쟁` belong
to the issue-card display layer, not this top-level filter list. In
DB-free/static fallback mode, it returns the sample category list below.

```json
{ "categories": ["정치", "경제", "환경", "기술", "세계"] }
```

## Error shape (all endpoints)

- `404` — unknown id, FastAPI default `{"detail": "..."}` shape (not yet
  normalized to the `ErrorResponse` schema in `app/schemas/issues.py` —
  flagged as a follow-up, low risk to change before frontend depends on it).
- `422` — invalid `window`/`sort` enum value. (This document previously said
  `400`; FastAPI's built-in `Query(pattern=...)` validation — which
  TASK-010 preserves unchanged — returns `422` with
  `{"detail": [...]}`, not `400`. Flagged as a pre-existing doc/implementation
  mismatch, not a TASK-010 regression; see `memory/known-issues.md`.)
- **No `503`.** TASK-010 implements the "degrade to last-known-good data"
  requirement (Technical Design §5, PRD §8.1) as `200` with the static
  sample dataset and an honest `data_as_of`, not a `503`, so the dashboard
  never has to render a hard-error state during a demo. This applies when
  `DATABASE_URL` is unset or unreachable, or when no `market_snapshots` rows
  exist yet (e.g. TASK-008 has not run) — see the FALLBACK NOTE in
  `app/api/routes/issues.py` and `reports/task-010-core-api-notes.md`.

## Wording alignment with `memory/glossary.md`

- `current_value` = "reflected expectation value" (never `price` or
  `probability` in the public API).
- `confidence_level` keeps its internal DB-aligned name in the JSON payload;
  the frontend is expected to display it as "Data reliability" per the
  glossary's use-carefully guidance — this API does not send display copy,
  only the raw enum.
- `related_events[].note` must always carry the "candidate, not cause"
  qualifier — enforced by convention here, not yet by a runtime filter
  (the banned-phrase filter itself is Data/AI scope, Service Design §6).
