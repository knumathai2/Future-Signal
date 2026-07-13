<!--
Purpose:        Threat model and approval-ready API/storage contract for scenario conversation
Owner:          Backend / PM / Reviewer
Update Trigger: Threat, retention, API, storage, or provider boundary changes
Harness Version: 1.1
-->

# TASK-125 — Scenario Conversation Threat and Contract

_Status: contract proposal complete; implementation approvals pending_
_Prepared: 2026-07-12_

## 1. Decisions

The first scenario-conversation release uses these fixed design choices:

- One anonymous session is scoped to one public issue.
- The model receives a server-built, read-only issue bundle and no tools.
- A session lasts at most 24 hours after creation.
- Conversation content is append-only during the session lifetime and is hard-
  deleted after expiry or an owner deletion request.
- The browser proves session ownership with a high-entropy bearer capability;
  the database stores only its hash.
- The session ID is an identifier, never authorization.
- Streaming uses authenticated `fetch` SSE, not a token in a URL and not native
  `EventSource`.
- Only complete validated paragraphs or lists are persisted and streamed.
- No user URL, file, image, live browser, database query, code execution, or
  external action is available to the model.
- The initial session has at most eight user turns and no model-authored context
  compaction.
- Active v8 and its public endpoints remain unchanged.

These decisions define the preferred implementation. They do not authorize the
public API or schema changes in Sections 7 and 8.

## 2. Assets and trust boundaries

### 2.1 Protected assets

- Provider and database credentials.
- System policy and internal configuration.
- Anonymous conversation content.
- Session capability tokens.
- Current issue definition, metric integrity, and premise classes.
- Other users' sessions.
- Provider budget and worker availability.
- Browser rendering integrity.
- Existing report, request, evidence, and market data.

### 2.2 Trust boundaries

```text
Browser (untrusted input and renderer)
  -> API edge (size, origin, rate, auth, schema)
  -> session/issue query boundary (object authorization)
  -> context builder (typed public facts and premise registry)
  -> isolated worker (one provider request, no tools)
  -> block validator (policy, leakage, refs, Markdown)
  -> ephemeral conversation storage
  -> authenticated fetch-SSE replay
  -> restricted Markdown renderer
```

External source excerpts are untrusted data even after their provenance is
accepted. User messages and all model output are untrusted at every later
boundary.

## 3. Identity and session ownership

### 3.1 Capability

Session creation returns:

- a UUID session ID; and
- a cryptographically random 256-bit bearer capability exactly once.

The browser holds the capability in memory and `sessionStorage` so a same-tab
reload can recover while a browser restart does not create durable history.
The raw capability must never appear in a URL, analytics event, error message,
application log, provider prompt, or database row.

The backend stores `SHA-256(capability)` and compares hashes in constant time.
Every session read, turn creation, stream, and deletion requires:

```text
Authorization: Bearer <session capability>
```

Issue ID + session ID + capability hash must all match. An invalid capability,
wrong issue, expired session, and unknown session share a non-enumerating public
failure shape.

### 3.2 Browser and request policy

- No cookie is required; CSRF exposure is therefore reduced, but CORS and
  origin checks remain mandatory.
- Allow only the configured Frontend origin and approved local origins.
- Never reflect an arbitrary origin with credentials.
- Set `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and a
  restrictive Content Security Policy.
- Do not bind the capability to IP or user-agent; that is brittle and adds
  tracking without replacing authorization.
- An owner deletion request invalidates the capability immediately.

## 4. Threat register

| ID  | Threat                                    | Impact                                        | Required controls                                                                                     | Required test                                                        |
| --- | ----------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| T01 | Direct policy override or roleplay bypass | Unsafe response or instruction disclosure     | Typed prompt blocks, permanent output validation, no secrets/authority in prompt                      | Direct, encoded, multilingual, misspelled, and roleplay corpus       |
| T02 | Injection inside accepted source text     | Policy drift or disclosure attempt            | Strip active content, bounded excerpt, explicit untrusted-data block, no source instructions executed | Stored excerpt containing override and exfiltration text             |
| T03 | Multi-turn premise poisoning              | Assumption becomes fact                       | Server-owned premise classes, no model promotion, no model-authored compaction                        | Five-plus-turn delayed trigger and pronoun reference                 |
| T04 | Cross-session object access               | Conversation disclosure or mutation           | Capability auth on every operation, issue/session scoping, non-enumerating errors                     | Read/append/stream/delete session B with session A token             |
| T05 | Capability leakage                        | Session takeover                              | No URL/log/provider exposure, hash at rest, 24-hour lifetime, CSP, owner deletion                     | Log/header/query inspection and browser XSS regression               |
| T06 | Model HTML/Markdown injection             | Script, tracking, or deceptive link execution | Raw HTML off, allow-list Markdown, no authored active links/images/forms/media                        | Script, image beacon, data URL, malformed link, bidi controls        |
| T07 | SSRF or internal URL access               | Internal service or metadata exposure         | No model/user URL fetch, existing safe-source pipeline only                                           | Local/private/credential-bearing URL corpus                          |
| T08 | Secret or private-data disclosure         | Credential or conversation exposure           | Minimal prompt, leakage validator, generic errors, no full-content logs                               | Secret-pattern canaries and provider-error simulation                |
| T09 | Resource and cost exhaustion              | Provider spend or outage                      | Per-message/session/IP/global limits, one in-flight turn, no auto-retry, stop switch                  | Oversized, concurrent, replay, reconnect, and distributed-rate cases |
| T10 | Duplicate/replay race                     | Duplicate spend or conflicting turns          | Idempotency key, unique sequence, immutable request identity, lease                                   | Same request submitted concurrently and after timeout                |
| T11 | Partial-stream publication                | Unsafe or broken browser output               | Complete-block validation and persistence before replay                                               | Chunk split inside Markdown, disconnect, malformed completion        |
| T12 | Retention failure                         | Unnecessary personal-data persistence         | 24-hour expiry, deletion state, cleanup verification, content-free aggregate metrics                  | Expiry/delete during idle, queued, and running states                |
| T13 | Stale or mismatched issue bundle          | Incorrect current fact                        | Definition/metric fingerprint, data time, issue scope, rebuild before call                            | Issue update between session and turn                                |
| T14 | Provider or dependency compromise         | Invalid output or data exposure               | Provider privacy review, pinned/approved dependencies, output distrust, kill switch                   | Provider malformed output and unavailable path                       |

The security design follows OWASP's prompt-injection, unsafe-output,
sensitive-data, excessive-agency, and unbounded-resource guidance:

- <https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html>
- <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
- <https://owasp.org/www-project-top-10-for-large-language-model-applications/2_0_vulns/LLM06_ExcessiveAgency.html>

## 5. Model context and premise state

The provider receives these typed blocks only:

1. fixed system and safety policy;
2. issue ID, title, category, exact definition revision, and resolution
   condition;
3. exact stored observations and data time;
4. accepted source excerpts and attribution metadata, already sanitized;
5. server-owned premise registry;
6. prior validated conversation turns within the session limits;
7. the latest untrusted user request.

It does not receive credentials, database rows outside the bundle, raw HTML,
internal exception text, other issues, other sessions, or hidden operational
metadata.

### 5.1 Premise registry

Each premise has an opaque ID, class, text, origin turn, and optional evidence
refs. The server enforces the class. Model output may reference existing IDs
and may propose new generic scenario text; the server always assigns new model
premises the `model_scenario` class.

The first release does not ask the model to summarize old turns for reuse.
When the eight-turn or cumulative-context limit is reached, the session stops
accepting new turns and offers a new session. This removes a high-risk semantic
compaction path from the initial implementation.

## 6. Limits and abuse controls

Initial constants, subject to TASK-130 measurement but not silent expansion:

| Limit                               |                                          Initial value |
| ----------------------------------- | -----------------------------------------------------: |
| User message                        |                               1,000 Unicode characters |
| Assistant answer                    | 2,500 Unicode characters and provider output-token cap |
| User turns per session              |                                                      8 |
| Cumulative stored conversation text |                              20,000 Unicode characters |
| In-flight turns per session         |                                                      1 |
| Session lifetime                    |           24 hours from creation; no sliding extension |
| Session creation per IP             |                           3 per 10 minutes; 20 per day |
| Turn creation per IP                |                          10 per 10 minutes; 60 per day |
| Provider attempts per turn          |                     1; no automatic safety/parse retry |
| Worker timeout                      |                 30 seconds pending measured evaluation |
| Validated response blocks           |                                             Maximum 12 |

The service also has a configurable global daily request and USD ceiling. When
either ceiling is reached, new turn requests fail before queueing. Raising any
limit or adding retry requires an explicit review because it changes cost and
attack exposure.

A multi-instance deployment requires a shared rate-limit state. In-memory
limits are acceptable only for a named local single-process prototype. The
shared mechanism is an infrastructure/dependency decision and remains
approval-gated. Rate-limit keys use a daily rotating keyed digest with a bounded
TTL; raw IP addresses are not retained in application logs or durable tables.

## 7. Proposed public API

All paths are proposals pending explicit public-interface approval. They do not
replace existing report endpoints.

### 7.1 Create session

`POST /api/issues/{issue_id}/scenario-sessions`

Request body:

```json
{}
```

Response `201`:

```json
{
  "session_id": "uuid",
  "session_capability": "returned once",
  "issue_id": "uuid",
  "created_at": "timestamp",
  "expires_at": "timestamp",
  "max_turns": 8,
  "policy_version": "summary-scenario-policy-1",
  "data_as_of": "timestamp",
  "caution_note": "server-owned text"
}
```

### 7.2 Read owned session

`GET /api/issues/{issue_id}/scenario-sessions/{session_id}`

Requires bearer capability. Returns session state, remaining turns, expiry,
data time, premise labels needed by the UI, and validated turns. It never
returns the capability hash, worker data, provider data, internal refs, or
unvalidated blocks.

### 7.3 Create turn

`POST /api/issues/{issue_id}/scenario-sessions/{session_id}/turns`

Headers:

```text
Authorization: Bearer <capability>
Idempotency-Key: <client-generated uuid>
```

Request:

```json
{
  "message": "user text"
}
```

Response `202`:

```json
{
  "turn_id": "uuid",
  "sequence": 1,
  "status": "queued",
  "requested_at": "timestamp",
  "stream_path": "/api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}/stream"
}
```

The API validates ownership, issue state, expiry, limits, idempotency, one-in-
flight rule, current bundle availability, and global budget before append. It
does not construct a provider client.

### 7.4 Read turn state

`GET /api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}`

Returns one of `queued`, `running`, `succeeded`, or `failed`, plus validated
response content only after success and one safe error code after failure.

### 7.5 Stream validated blocks

`GET /api/issues/{issue_id}/scenario-sessions/{session_id}/turns/{turn_id}/stream`

The Frontend opens this path with `fetch` and the authorization header, then
parses `text/event-stream`. Native `EventSource` is not used because it cannot
set the bearer header and placing the capability in the query string is
forbidden.

Events:

- `snapshot`: owned turn state and replay cursor;
- `block`: one complete validated paragraph or list;
- `complete`: final response metadata;
- `failed`: safe failure code;
- `heartbeat`: no content.

Reconnect uses `Last-Event-ID` in the authenticated fetch request. Raw provider
chunks never become SSE events.

### 7.6 Delete session

`DELETE /api/issues/{issue_id}/scenario-sessions/{session_id}`

Requires bearer capability and returns `204`. It immediately appends a deletion
state, invalidates authorization, prevents new blocks, and causes the cleanup
worker to remove conversation content. Existing public issue/report data is
untouched.

### 7.7 Error contract

| HTTP | Safe code                | Meaning                                                                                   |
| ---: | ------------------------ | ----------------------------------------------------------------------------------------- |
|  400 | `invalid_request`        | Invalid request shape or sequence                                                         |
|  401 | `session_token_required` | Missing or malformed authorization header                                                 |
|  404 | `session_unavailable`    | Unknown, mismatched, expired, deleted, or unauthorized session without enumeration detail |
|  409 | `turn_in_progress`       | One turn is already queued or running                                                     |
|  409 | `session_limit_reached`  | Turn/context limit reached                                                                |
|  413 | `message_too_large`      | Input exceeds the fixed limit                                                             |
|  422 | `request_not_supported`  | Request cannot be handled under the scenario policy                                       |
|  429 | `rate_limited`           | Session/IP/global request bound reached                                                   |
|  503 | `generation_unavailable` | Worker, provider, or global budget unavailable                                            |

No error returns a provider body, stack, policy rule text, capability state, or
database detail.

## 8. Proposed storage

TASK-126 may create one new append-only migration only after schema approval.
Preferred tables:

### `scenario_sessions`

- `id` UUID primary key
- `market_id` UUID foreign key
- `capability_hash` fixed 64-character digest, unique
- `definition_ref` and `input_fingerprint`
- `policy_version` and `input_schema_version`
- `created_at`, `expires_at`, `deleted_at` nullable
- no raw capability, IP address, user agent, or provider content

### `scenario_turns`

- `id` UUID primary key
- `session_id` UUID foreign key
- unique `(session_id, sequence_number)`
- unique `(session_id, idempotency_key_hash)`
- `role` restricted to user or assistant
- validated text content
- `created_at`
- immutable during lifetime

### `scenario_premises`

- opaque premise ID and session foreign key
- class enum from TASK-124
- normalized text
- origin turn foreign key
- optional exact evidence refs
- immutable; no promotion/update operation

### `scenario_generation_requests` and `scenario_generation_events`

- immutable request identity, exact session/turn/fingerprint
- append-only queued/running/succeeded/failed events
- expiring lease and bounded attempt number
- safe error code, aggregate token/cost/timing only
- no full provider prompt or raw response

### `scenario_response_blocks`

- request foreign key, consecutive sequence, block type
- already-validated paragraph/list JSON
- created timestamp
- unique request/sequence

### 8.1 Deletion and audit

Conversation content is append-only only while live. Expiry or owner deletion
removes session, turn, premise, request, event, and block rows in one bounded
cleanup transaction. The system may retain content-free daily aggregates such
as counts, latency, rejection category, and cost, but no session ID, capability
hash, message hash, premise, source excerpt, or conversation text.

The cleanup process records aggregate deleted-row counts and earliest/latest
expiry only. It never logs content. Cleanup scheduling is infrastructure work
and must be approved before deployment.

## 9. Output and browser contract

The model produces a minimal internal envelope, not a visible template:

```json
{
  "answer_markdown": "free-form response",
  "premise_refs": ["opaque premise id"],
  "new_scenario_premises": ["generic conditional premise"]
}
```

The server validates refs and forces every new item to `model_scenario`. Server-
owned response metadata adds response ID, data time, policy version, and
caution.

Allowed Markdown is limited to paragraphs, unordered/ordered lists, and
emphasis. Raw HTML, headings that impersonate system UI, images, links, tables,
block quotes, code, embedded media, forms, and custom attributes are removed or
rejected. Accepted source links render in a separate server-owned area.

## 10. Worker and failure behavior

- The API appends or joins an immutable turn request and returns immediately.
- A separate worker claims one lease and rebuilds the issue/session bundle.
- Fingerprint or expiry change before the call fails safely.
- One provider call emits bounded text chunks; the worker buffers complete
  paragraph/list blocks.
- Each block passes shape, premise-ref, data, policy, leakage, and Markdown
  validation before storage.
- The final envelope reruns full-response validation.
- Any failure removes the current partial response from the public session;
  earlier successful turns remain.
- Deletion requested during a call prevents later persistence and delivery.
- No automatic provider retry occurs.

## 11. Logging and provider privacy

Operational logs may contain request/session correlation IDs, status, safe
error code, character/token counts, timing, rejection category, and estimated
cost. They may not contain capabilities, messages, answers, source excerpts,
premises, full prompts, raw responses, credentials, or database configuration.

Before a provider evaluation, record:

- provider/model identity;
- whether submitted content is retained or used for model improvement;
- configured retention/training controls;
- data-processing region if available;
- maximum request size and timeout;
- exact evaluation count and USD ceiling.

The UI warns users not to enter personal, confidential, or identifying
information. The product does not promise that a model can reliably remove such
content after submission; prevention and bounded retention are the primary
controls.

## 12. Security test plan

### Authentication and isolation

- Wrong, missing, expired, deleted, and cross-issue capability.
- Session A token against every session B endpoint.
- Capability absent from logs, URLs, provider input, and analytics.
- Concurrent delete and generation completion.

### Injection and state integrity

- Direct/indirect, encoded, Unicode, multilingual, roleplay, delayed, and
  best-of-N-style variations.
- Source excerpt containing instructions and active markup.
- User assumption referred to with pronouns five turns later.
- Request to recast a model scenario as accepted information.
- Secret-pattern canary in system-only context.

### Browser and transport

- Script tags, event handlers, image beacons, data/javascript URLs, bidi and
  invisible controls, malformed Markdown, oversized blocks.
- Authenticated fetch-SSE replay, duplicate event, gap, reconnect, and failure.
- CORS preflight and disallowed-origin requests.

### Cost and availability

- Message/session/global size boundaries.
- One-in-flight enforcement and idempotent duplicate joins.
- Session/IP/global request ceilings.
- Provider timeout, malformed response, disconnect, and budget stop.
- Expiry cleanup with idle, queued, running, completed, and deleted sessions.

## 13. Approval packet

TASK-125 requests separate approval before TASK-126 implementation for:

1. The proposed public paths, bearer-capability contract, authenticated fetch-
   SSE behavior, and safe error shapes in Section 7.
2. One append-only migration containing the tables in Section 8, plus the
   explicit 24-hour hard-deletion exception for ephemeral conversation data.
3. Session limits in Section 6 as initial security constants.
4. A future cleanup schedule and shared multi-instance rate-limit mechanism;
   the specific infrastructure/dependency choice remains separately gated.

This document does not request or authorize migration application, a provider
call, dependency installation, infrastructure mutation, deployment, production
write, or active-v8 transition.

## 14. TASK-126 handoff

After explicit API/schema approval, TASK-126 should implement only models,
append-only migration, auth helpers, request/event state, cleanup logic behind
a disabled feature flag, and deterministic tests. The migration remains
unapplied. Provider and Frontend work stay in later tasks.
