# TASK-099: On-demand issue briefing policy and execution plan

Date: 2026-07-11  
Owner: PM / Planner  
Branch: `pm/TASK-099-ai-briefing-policy-reset`  
Status: Planning contract ready for approval  

## 1. Decision summary

The next report program will replace collection-time summary generation with
an explicit user-requested, cache-backed issue briefing flow. Market-data
collection, external-context collection, and briefing generation become three
independent responsibilities.

The writer prompt will primarily explain how to produce a useful briefing.
Evidence integrity and the small set of product-safety boundaries will be
enforced outside the prose-writing instructions wherever deterministic code is
more reliable.

The output retains a stable envelope and broad section categories, while the
writer may choose the number, order, titles, paragraph/list style, and internal
composition of sections according to the available evidence.

V1-v6 contracts remain available as historical records during the transition.
After the new contract passes development evaluation, their active-policy
references and runtime implementations may be removed in a separately reviewed
cleanup task. Append-only report and decision history remains available for
audit.

## 2. Product intent

The AI acts as an issue briefing writer. A useful result helps a reader
understand:

- what the issue is;
- what is currently established by available sources;
- what the observed market data shows;
- how the market data and external context differ as evidence;
- which interpretations remain conditional or uncertain; and
- which future announcements, documents, dates, or data updates are useful to
  check.

The service does not generate a briefing merely because a collector stored a
new snapshot. A user explicitly requests the briefing from the issue-detail
screen.

## 3. Target architecture

```text
Polymarket/API collection
        -> normalized markets, snapshots, metrics, signals
        -> no AI briefing generation

External-context collection
        -> broad source discovery
        -> lightweight relevance/provenance checks
        -> source level + supported claims
        -> reusable context store

Issue detail screen
        -> render observed data and available source cards
        -> user selects "AI briefing generation"
        -> POST generation request
        -> cache/fingerprint check
              -> fresh: return the cached briefing
              -> stale: keep last good briefing visible and enqueue refresh
              -> missing: enqueue first generation and return generating state
        -> worker builds the latest evidence bundle
        -> optionally refreshes missing/stale context within bounded limits
        -> generates, validates, stores, and returns the briefing
```

The recommended request model is asynchronous. It avoids holding an HTTP
connection open during research and writing, and it permits deduplication,
budget controls, retries, and last-known-good behavior.

## 4. Responsibility boundaries

### 4.1 Market-data collector

The collector owns source fetch, normalization, snapshots, metrics, signals,
and collection health. A report-provider failure cannot affect this path.

### 4.2 External-context collector

The context collector owns source discovery, normalization, deduplication,
source classification, supported-claim extraction, and refresh timing. It can
run periodically for important issues and in a bounded refresh mode after a
user briefing request.

Context collection does not itself write a briefing. The same collected source
may support later briefings without another search call when it remains fresh.

### 4.3 Briefing generation service

The generation service owns cache selection, evidence-bundle construction,
writer invocation, output validation, append-only report storage, and
last-known-good selection. It is invoked only by an explicit generation
request or an approved manual development evaluation, not by the normal data
collector.

### 4.4 Frontend

The issue-detail screen owns the explicit generation control and the states
`idle`, `generating`, `fresh`, `stale`, and `failed_with_last_good`. The user can
continue reading deterministic data while a briefing is generated.

## 5. Positive-first writer prompt

The prompt should devote most of its instruction budget to the desired result.
The initial prompt direction is:

```text
You are an issue briefing writer helping a general reader understand the
current issue quickly and accurately.

Begin by explaining what the issue is and why its stated condition matters.
Summarize the current situation using the supplied source material.
Explain the observed market-data movement in clear language.
Keep market observations and external-source information visibly distinct.
Connect every factual statement to the evidence that supports it.
Describe multiple interpretations when the available evidence supports more
than one reading.
Express unresolved points with appropriately conditional language.
Tell the reader which announcements, documents, dates, or data updates would
help clarify the issue next.
Use natural, concrete Korean and organize the material for easy reading.
Adapt the number and order of sections to the evidence actually available.
```

The final prompt may include a short service-boundary paragraph, but it will
not repeat long lists of prohibited words, fixed sentence tokens, overlap
thresholds, or historical v3-v6 field rules. Deterministic checks own evidence
IDs, stored metrics, URLs, and response-shape integrity.

## 6. Flexible output contract

The stable public envelope is proposed as:

```json
{
  "status": "fresh",
  "report_version": "v7",
  "headline": "string",
  "summary": "string",
  "sections": [
    {
      "type": "issue_overview",
      "title": "string",
      "content": "string",
      "format": "paragraph",
      "evidence_refs": ["market_definition:...", "source:..."]
    }
  ],
  "sources": [],
  "generated_at": "timestamp",
  "data_as_of": "timestamp",
  "context_as_of": "timestamp",
  "cache": {
    "state": "fresh",
    "input_fingerprint": "opaque string"
  }
}
```

Allowed broad section types are:

- `issue_overview`
- `current_context`
- `market_data`
- `external_context`
- `uncertainties`
- `what_to_watch`

The envelope, evidence references, timestamps, and source records are strict.
The following are flexible:

- section count and order;
- section title;
- paragraph or short-list presentation;
- amount of detail within configured total bounds;
- omission of a section whose evidence is unavailable; and
- issue-specific organization of conditional interpretations.

Numbers, dates, proper names, and source-supported current facts are permitted
when the corresponding evidence reference is valid. Deterministic market
values remain backend-owned so they can be checked exactly and rendered
consistently.

## 7. Broader context collection with simpler verification

### 7.1 Discovery policy

Queries may use the issue title, named entities, institutions, resolution
condition, relevant dates, category terms, and language variants. Collection
prioritizes official/public records, established reporting, and specialist
institutions, while retaining useful single-source context with a visible
source level.

### 7.2 Source levels

| Level | Meaning | Permitted use |
|---|---|---|
| A | Official or primary source | Established facts and direct statements |
| B | Established reporting or recognized institution | Current context and attributed reporting |
| C | Relevant single-source or supporting material | Clearly labelled supporting context |
| D | Inaccessible, unrelated, generated, or materially unsupported | Internal rejection/audit only |

One official source can support the claim it directly contains. Two independent
sources are useful corroboration, not a universal publication prerequisite.
The UI and briefing retain the source level and attribution instead of treating
all accepted material as equally verified.

### 7.3 Default checks

The normal path checks:

- URL and document accessibility;
- source identity and type;
- issue/entity/condition relevance;
- publication or effective time;
- the specific claim supported by the document;
- duplicate or syndicated content; and
- obvious contradiction with stronger available evidence.

A separate verifier-model call is reserved for conflicts, high-impact claims,
ambiguous relevance, or strong causal/outcome language. It is not mandatory
for every accessible source.

### 7.4 Relationship language

The system represents the evidence level instead of applying a universal
no-relationship statement to every source:

- an observed timing overlap is described as timing only;
- a source's interpretation is attributed to that source;
- corroborated context may be synthesized with conditional language; and
- the service does not invent a causal conclusion beyond the supplied support.

This policy change requires an explicit amendment to the current binding
wording and automated-context rules before implementation.

## 8. Validation policy

### 8.1 Blocking validation

Storage/publication is blocked for:

- unknown or mismatched evidence references;
- fabricated source URLs, titles, claims, metrics, dates, or entities;
- factual prose that materially conflicts with its cited evidence;
- an invalid public envelope or unsafe link;
- direct user inducement outside the information-briefing purpose; or
- a generation result that cannot be reconstructed against stored inputs.

### 8.2 Quality warnings

The following normally produce diagnostics, not total report rejection:

- moderate repetition;
- generic or less polished prose;
- section-count preference;
- English terms;
- sentence-length preference;
- section ordering;
- conditional-word choice; and
- non-critical overlap between sections.

Quality metrics remain valuable for evaluation and prompt improvement, but do
not masquerade as evidence or safety failures.

## 9. Cache and request behavior

The cache fingerprint should include at least:

```text
issue_id
+ latest_metric_id
+ market_definition_revision
+ accepted_context_revision
+ prompt_version
+ policy_version
+ input_schema_version
```

Recommended API operations:

- `GET /api/issues/{id}/report` returns the latest valid state and last good
  result when available.
- `POST /api/issues/{id}/report/generate` creates or joins an idempotent
  generation request.
- `GET /api/issues/{id}/report/requests/{request_id}` returns generation state
  when polling is needed.

Repeated clicks for the same fingerprint join one request. Per-issue cooldown,
per-run and cumulative budget limits, request timeouts, and a worker lease
prevent uncontrolled calls. A stale last-good report remains readable with
honest timestamps while refresh is in progress.

A new append-only request/lease table is recommended so worker recovery does
not depend on in-process background tasks. PostgreSQL row locking can provide
the first worker implementation without adding Redis or a queue dependency.

## 10. Historical-contract transition

1. Copy v1-v6 policy/shape summaries into
   `docs/archive/ai-report-contracts/` with version, ADR, active dates, and
   supersession reason.
2. Mark v1-v6 sections in active product documents as historical references,
   not current writer instructions.
3. Keep legacy DB rows read-only for audit while v7 runs in development.
4. After v7 evaluation passes, remove v1-v6 generation, parsers, fixtures, and
   inactive tests in a dedicated cleanup task.
5. Retain migrations, ADRs, and minimal schema/history readers required to
   explain old stored records.

No historical implementation is deleted as part of this planning task.

## 11. Work sequence

| Task | Owner | Deliverable | Gate |
|---|---|---|---|
| TASK-099 | PM | This policy, architecture, transition, and approval packet | Documentation only |
| TASK-100 | PM / Reviewer | Constraint inventory and v1-v6 archive map | No runtime change |
| TASK-101 | PM / Data-AI | Positive prompt, flexible v7 envelope, evidence-level policy | Explicit AI/wording-policy approval |
| TASK-102 | Backend | Append-only generation-request schema and worker contract | Explicit schema approval |
| TASK-103 | Data-AI | Broad context collection and lightweight verification | Provider/budget and policy approval |
| TASK-104 | Backend / Data-AI | Remove report generation from normal collection and add on-demand service | Workflow/runtime approval |
| TASK-105 | Backend | Generate/status/read API implementation | Explicit public API approval |
| TASK-106 | Frontend | Button, generation states, flexible section/source rendering | TASK-105 |
| TASK-107 | Reviewer | Local fixture, failure, concurrency, cache, wording, and evidence review | No deployment |
| TASK-108 | Data-AI / Reviewer | Bounded development v6-v7 comparison | Paid-call and development-write approval |
| TASK-109 | Reviewer | Legacy runtime cleanup proposal or execution | v7 acceptance; separate deletion approval |

Only one task is in progress at a time. Implementation begins with TASK-100
after the planning packet is accepted.

## 12. Approval packet

The user has approved documenting and preparing this direction. The following
implementation authorities should be confirmed together before TASK-101-108:

1. replace the active negative-first wording/AI policy with this positive-first
   evidence policy;
2. permit A-C source levels with visible attribution instead of the current
   universal strict verified-only publication gate;
3. add an append-only generation-request/lease migration;
4. change the public report API to generation/status/cache states;
5. remove AI report generation from the normal scheduled collection path;
6. allow bounded local/development context and writer calls under a recorded
   budget; and
7. append only local/development context, request, and report records.

Deployment, production writes, new dependencies, and legacy-runtime deletion
remain separate approval points.

## 13. Acceptance criteria for implementation readiness

- One active policy clearly distinguishes evidence integrity from style
  preferences.
- The writer prompt is predominantly positive, task-oriented guidance.
- Market collection can complete with no report provider configured.
- A briefing is generated only after an explicit user request or approved
  development evaluation.
- Context collection exists independently and can reuse fresh stored sources.
- Accepted sources expose their level and supported claims.
- The v7 envelope supports flexible sections without losing evidence links.
- Duplicate user requests produce one provider operation.
- Cache freshness is based on input revisions, not time alone.
- Last-known-good behavior is defined for every provider and validation
  failure.
- V1-v6 contracts have a documented archive and separately gated cleanup path.

