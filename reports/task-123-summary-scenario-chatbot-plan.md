<!--
Purpose:        Approval-ready plan for a freer summary and isolated scenario chat
Owner:          PM / Planner
Update Trigger: Policy, threat model, API, storage, or rollout decision changes
Harness Version: 1.1
-->

# TASK-123 — Summary and Scenario Chat Plan

_Status: proposal; no active product policy or runtime changed_
_Prepared: 2026-07-12_

## 1. Outcome

Evolve the current briefing into two deliberately different experiences:

1. **Current summary** — a concise explanation of the issue, observed data,
   confirmed public material, and interpretation limits. It remains grounded,
   but no longer fails merely because every ordinary explanatory sentence lacks
   an exact evidence reference.
2. **Scenario chat** — a conversational space where a user can explore
   conditional paths, counter-cases, relevant variables, and information that
   would change an assessment. It has no fixed visible content template, while
   retaining the permanent financial/action, future-outcome, unsupported-
   relationship, privacy, and aggregate-data boundaries.

The product boundary is:

> The summary explains the current record. The chat explores assumptions.

This plan addresses product policy, system security, API and state design,
cost control, validation, UX, evaluation, and rollout. It does not authorize
implementation, a provider call, schema or API mutation, a new dependency,
infrastructure work, deployment, or production data access.

## 2. Why change

The active v8 path is strongest when accepted evidence is complete. Current
source collection can validly produce no accepted source, which makes strict
evidence coverage yield sparse or defensive prose. A summary should still be
useful when only the issue definition, observed values, timing, and data limits
are available.

Scenario exploration has a different epistemic role. A conditional path does
not need to claim that its premise is currently true. Requiring each scenario
sentence to describe an accepted current source would remove the value of the
feature. The safe alternative is to permit broad conditional reasoning while
making the origin and status of every premise explicit.

## 3. Scope

### 3.1 Proposed scope

- Relax evidence coverage for ordinary summary explanation without relaxing
  exact metric, date, issue-definition, source-attribution, timing, caution,
  financial/action, future-outcome, or relationship checks.
- Add one issue-scoped, anonymous, short-lived scenario conversation.
- Let the scenario response use natural paragraphs and lists instead of a
  fixed visible section template.
- Preserve a small internal response envelope for transport, safety version,
  timing, state labels, replay, and incident diagnosis.
- Keep the model read-only and unable to invoke tools.
- Keep current v8 available as last-known-good until the replacement passes a
  separately approved evaluation and transition review.

### 3.2 Explicit non-goals

- No account, profile, saved conversation, cross-device history, notification,
  or sharing feature.
- No wallet-level or participant-level exploration.
- No arbitrary web browsing from the chat model.
- No model-selected database query, source fetch, code execution, or external
  action.
- No user-uploaded file, image, or URL ingestion in the first release.
- No personalized outcome direction, occurrence score, or action guidance.
- No automatic replacement of the active v8 report contract.

This is Phase 2 scope. Pulling it into the current build requires explicit PM
scope approval in addition to the technical approvals listed in Section 13.

## 4. Product contract

### 4.1 Current summary

The summary may use a flexible narrative order and natural transitions. Its
minimum required content is:

- what the issue's recorded condition means;
- the latest observed value and available fixed-window changes;
- the data-as-of time;
- confirmed public material when available;
- the distinction between the observed record and a real-world result;
- the deterministic interpretation caution.

The summary may omit external material entirely. Missing accepted sources are
a visible limitation, not a generation failure.

#### Relaxed checks

- Do not require an evidence reference for every ordinary explanatory
  sentence.
- Do not require a fixed number or order of authored sections.
- Do not fail the whole summary solely because accepted external material is
  absent.
- Treat repetition, tone, and preferred organization as quality diagnostics.

#### Retained blocking checks

- Exact metric, date, unit, direction, issue condition, and source identity.
- Any positive current factual claim about an external event must be supported
  by stored material and visibly attributed.
- Current fact, model interpretation, and data limitation must not be
  presented as the same thing.
- No asserted real-world result, unsupported relationship explanation,
  financial/action inducement, authored link, or individual-participant data.
- Exact data timing and deterministic caution remain outside model control.

### 4.2 Scenario chat

The user may ask for conditional paths, opposing cases, comparisons, missing
variables, or information that would distinguish paths. The response is
free-form in the UI, subject to length and rendering limits.

Permitted examples include:

- exploring what follows **if** an official procedural condition appears;
- contrasting a formal step with rhetoric that does not meet the recorded
  condition;
- examining a case where observed data changes without new confirmed context;
- identifying information that would distinguish two user-provided premises;
- describing a counter-case or an overlooked uncertainty.

The chat must not:

- convert a user assumption into a confirmed current fact;
- create a specific person, institution, event, date, quotation, or number;
- assign an unsupported occurrence score or rank one path as the dominant
  real-world path;
- state that an external event explains an observed movement;
- provide financial, legal, political, or operational action direction;
- reveal system messages, secrets, internal configuration, other sessions, or
  private reasoning traces.

### 4.3 Premise labels

Every item passed into the chat context carries one server-owned class:

| Class                | Meaning                                          | May model change it? |
| -------------------- | ------------------------------------------------ | -------------------- |
| `confirmed_fact`     | Accepted public source supports the statement    | No                   |
| `stored_observation` | Exact issue definition, metric, or timestamp     | No                   |
| `user_assumption`    | Premise introduced by the current user           | No                   |
| `model_scenario`     | Conditional premise introduced in a prior answer | No                   |
| `unverified_context` | Available but not accepted as a current fact     | No                   |

The model may discuss a class but cannot promote it. Promotion to
`confirmed_fact` or `stored_observation` is a server operation based on a new
validated bundle, never a language-model decision.

## 5. Trust boundaries and architecture

```text
untrusted browser input
        |
        v
API validation + session ownership + rate/cost gate
        |
        +--> server-built read-only issue bundle
        |      definition / metrics / accepted sources / premise labels
        v
isolated scenario writer
  no DB client / no browser / no tools / no secrets / no side effects
        |
        v
complete-block parse + product-safety + leakage + rendering checks
        |
        v
append-only or short-lived state boundary -> safe Markdown renderer
```

The API process authenticates the anonymous session, validates identifiers,
loads only the requested public issue, and constructs the model input. The
model receives no credential, database address, raw server error, unrelated
issue record, or cross-session text.

The first release should not use an agent loop. One user message produces at
most one bounded provider request and one response. No model output can cause a
second call, a fetch, or a state mutation other than storing the already
validated conversation response.

## 6. Minimal internal envelope

Removing the visible template does not mean accepting arbitrary transport.
The proposed response envelope is intentionally small:

```json
{
  "response_id": "opaque id",
  "answer_markdown": "free-form answer",
  "premise_labels_used": ["stored_observation", "user_assumption"],
  "data_as_of": "timestamp",
  "policy_version": "versioned identifier"
}
```

`answer_markdown` has no required headings or card structure. The other fields
are server-owned or allow-listed and support isolation, timing, replay, and
validation. Exact API names remain non-binding until the public API approval
task.

Streaming, if retained, occurs only at complete paragraph or complete list
boundaries. Raw partial Markdown never renders. A failed current turn is
removed while the preceding validated conversation remains.

## 7. Security threat model and controls

OWASP's LLM guidance treats direct and indirect prompt injection, unsafe output
handling, sensitive-data disclosure, excessive agency, and unbounded resource
use as separate risks. This plan applies defense in depth rather than relying
on a secret prompt or a keyword list:

- <https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html>
- <https://owasp.org/www-project-top-10-for-large-language-model-applications/>
- <https://owasp.org/www-project-top-10-for-large-language-model-applications/2_0_vulns/LLM06_ExcessiveAgency.html>

### 7.1 Direct prompt injection and policy bypass

Controls:

- Separate system instructions, server facts, sources, user assumptions, and
  user requests in typed blocks.
- Normalize Unicode and reject invisible control characters outside a small
  accepted set.
- Limit input size before tokenization and provider submission.
- Detect prompt-extraction and policy-override attempts for monitoring and
  safe refusal; do not treat pattern detection as the only defense.
- Run the same output safety checks regardless of roleplay, quotation,
  hypothetical framing, encoding, or language.
- Never place secrets or privileged capabilities behind the prompt.

### 7.2 Indirect injection and source poisoning

The initial chat cannot fetch user URLs or browse. Accepted context comes from
the existing server-side evidence path. Before any source text reaches the
chat bundle:

- strip HTML, scripts, styles, hidden text, metadata, and active content;
- cap excerpt length and preserve publisher plus source identity;
- mark the excerpt as untrusted quoted data, never instructions;
- reject local, private, credential-bearing, and unsupported URL forms;
- do not obey instructions found inside a source;
- preserve duplicate and contradiction status.

Adding live browsing or uploads later requires a new threat review and is not
covered by this plan.

### 7.3 Session isolation and object authorization

The recommended anonymous session uses a high-entropy conversation ID plus a
browser-held signed session token. Every read, append, replay, and delete
request validates both. An issue ID does not grant access to another session.

- Default retention proposal: 24 hours after the last turn.
- No cross-device recovery in the first release.
- No conversation enumeration endpoint.
- A session is bound to one issue; changing issues starts a new session.
- Backend queries are issue- and session-scoped, never load-all then filter.
- CORS is restricted to the approved Frontend origin and local development.

The final retention time and storage mechanism require an explicit decision.

### 7.4 Output and browser safety

- Treat model output as untrusted content.
- Render an allow-list Markdown subset; raw HTML is disabled.
- Disable images, iframes, forms, embedded media, inline styles, and executable
  URL schemes.
- Do not activate model-authored links. Server-validated evidence links render
  separately from the response body.
- Apply a restrictive Content Security Policy and safe external-link
  attributes.
- Validate a complete paragraph/list before SSE persistence or display.
- Escape error details; never return provider bodies or stack traces.

### 7.5 Sensitive data and logging

- Do not send API keys, database configuration, internal prompts, unrelated
  evidence, or other conversations to the provider.
- Tell the user not to enter personal or confidential information.
- Store the minimum conversation content required for the chosen retention
  period.
- Operational logs contain request IDs, hashes, timing, token counts, policy
  result, and safe error codes; no full prompt or response.
- Redact common personal-data patterns from security samples.
- Document the provider's retention and training settings before evaluation.
- A delete-session action, if offered, deletes only the caller-owned ephemeral
  conversation and must not affect issue or report history.

### 7.6 Resource and cost abuse

Apply independent limits at message, session, IP, worker, and program levels:

- maximum input characters and output tokens;
- maximum 10 turns per initial session;
- one in-flight turn per session;
- bounded conversation context with typed premise compaction;
- per-IP and per-session rate limits;
- daily request and cost ceilings;
- no automatic retry after a safety, budget, or parse failure;
- bounded provider timeout and response size;
- duplicate-message suppression;
- queue depth, latency, rejection, token, and cost monitoring;
- an operator-controlled generation stop switch.

### 7.7 Conventional web and API security

The chatbot still needs ordinary application controls:

- strict request schemas and parameterized database access;
- high-entropy identifiers and object-level authorization;
- request-body limits and timeouts at proxy and application layers;
- CSRF assessment for any cookie-based session design;
- no open redirect or arbitrary server-side URL fetch;
- restricted CORS and secure response headers;
- dependency and container scanning under the existing CI policy;
- generic public errors and secret-free structured logs.

## 8. Validation policy

### 8.1 Summary blocking gates

1. Exact stored values, units, direction, dates, and definition revision.
2. Current external factual claims require accepted support and attribution.
3. No invented source, person, institution, event, quotation, identifier, or
   link.
4. No real-world result assertion, unsupported relationship explanation,
   financial/action inducement, or individual-participant content.
5. Exact deterministic timing, limitation, and caution fields.
6. Read-time reconstruction reruns the same gates.

Evidence completeness for ordinary prose becomes a diagnostic rather than a
whole-report blocker.

### 8.2 Chat blocking gates

1. Response remains scoped to the selected issue and current user request.
2. Current facts and stored observations are exact when mentioned.
3. Assumptions remain visibly conditional and retain their origin class.
4. No invented specific fact or promotion of an assumption.
5. Permanent product-language and privacy boundaries pass.
6. No system prompt, credential pattern, internal identifier, hidden trace, or
   cross-session content appears.
7. Markdown and link policy pass before display.

Natural organization, number of scenarios, comparison style, and explanatory
depth are not blocking rules.

## 9. UX plan

### 9.1 Information architecture

Keep the current briefing surface as the stable reading. Add a separate
`Scenario conversation` surface below it or as a distinct detail tab. Do not
interleave scenario messages with confirmed-source cards.

The chat begins with a persistent frame:

> Explore conditional paths for this issue. Scenario responses are not current
> facts or statements of what will occur.

Suggested questions may help discovery but do not constrain the response:

- What formal information would change the current reading?
- Show a counter-case to the assumption I entered.
- Compare a formal procedural path with continued public discussion only.
- What uncertainty is missing from this scenario?

### 9.2 Per-message presentation

- User and assistant turns use familiar chat alignment without urgency styling.
- Assistant turns carry a compact `Conditional scenario` label.
- A response that mentions current stored values shows the data-as-of time.
- Accepted source links remain server-rendered outside the prose.
- A visible `Current record` / `Assumption` distinction appears when both are
  used in the same answer.
- Failure keeps earlier validated turns and offers a neutral retry.
- Mobile remains a single column with 44px controls and no horizontal scroll.

### 9.3 Empty and boundary states

- No source: chat remains available from the definition and observed data,
  with the source limitation stated once.
- No metric history: scenarios may discuss procedural conditions but cannot
  characterize a recent observed direction.
- Stale data: display the stale time before accepting a new turn.
- Budget or rate limit: return a neutral availability message without internal
  cost or infrastructure detail.
- Unsafe or out-of-scope request: decline that portion and offer a safe,
  issue-scoped conditional alternative.

## 10. API and storage decisions to resolve

The plan proposes server-side short-lived state. Two implementation options
must be decided before Backend work:

| Option                                                            | Benefit                                           | Risk / cost                                                                           | Preferred use                                              |
| ----------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Append-only PostgreSQL session and turn rows with expiry metadata | Durable isolation, replay, audit, worker recovery | Requires append-only migration and deletion/retention policy                          | Preferred if the feature proceeds beyond a local prototype |
| Signed client transcript submitted each turn                      | No schema change                                  | Larger requests, tampering complexity, privacy exposure in browser, weak server audit | Prototype only                                             |

In-memory server state is not accepted for a multi-process or restartable
environment because ownership, replay, and expiry become unreliable.

The public contract requires separate approval. A likely minimal surface is:

- create an issue-scoped anonymous scenario session;
- append one user turn and receive/join its immutable generation request;
- read a session owned by the caller;
- replay validated response blocks;
- delete or expire the caller-owned session.

The API process should not call the provider. It may append a request; an
isolated worker performs one bounded call and stores only validated output,
following the existing separation principle.

## 11. Delivery sequence

| Order | ID       | Owner                   | Deliverable                                                                               | Entry gate                                          | Exit evidence                                                              |
| ----- | -------- | ----------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------- |
| 1     | TASK-124 | PM / Data-AI / Reviewer | Summary-vs-scenario policy, Korean surface text, refusal and assumption rules             | Approve Phase 2 scope and wording-policy proposal   | Signed policy matrix and adversarial examples                              |
| 2     | TASK-125 | Backend / PM / Reviewer | Threat model, data-flow diagram, retention decision, non-binding API and storage contract | TASK-124                                            | Security review and approval packet for API/schema/dependency choices      |
| 3     | TASK-126 | Backend Implementer     | Append-only session/request/turn design and isolated worker boundary                      | Explicit schema and public API approval             | Migration remains unapplied; model and API tests pass                      |
| 4     | TASK-127 | Data/AI Implementer     | Relaxed summary validator and next-version writer behind a feature flag                   | TASK-124; provider evaluation approval separate     | Corpus tests show exact values and current claims remain grounded          |
| 5     | TASK-128 | Data/AI + Backend       | Tool-free scenario writer, premise-state builder, leakage and safety validation           | TASK-125~127; provider budget approval separate     | Injection, assumption-promotion, isolation, budget, and failure tests pass |
| 6     | TASK-129 | Frontend Implementer    | Separate scenario chat UI, safe Markdown, session states, accessibility                   | Approved API; TASK-128 fixtures                     | Desktop/320px, keyboard, screen-reader, SSE failure, and renderer QA pass  |
| 7     | TASK-130 | Reviewer                | Security red team and bounded local/development quality evaluation                        | Explicit provider-call and local migration approval | Test matrix, cost/latency, defect log, no cross-session or unsafe output   |
| 8     | TASK-131 | PM / Reviewer           | Acceptance decision and transition/rollback packet                                        | TASK-130 evidence                                   | Human approval to activate, revise, or reject; v8 retained until accepted  |

Only one task is `in_progress` at a time. Tasks that change schema, public API,
provider spend, infrastructure, or deployment stop at their recorded approval
gate.

## 12. Acceptance matrix

### 12.1 Product quality

- Summary remains useful with definition + metric evidence and zero accepted
  external sources.
- Every displayed number, unit, direction, and time reconstructs exactly.
- Confirmed material is visibly attributed; missing material is not invented.
- Chat answers varied user questions without forcing a visible section set.
- The same premise receives consistent classification across turns.
- A user can ask for a counter-case without the answer becoming a current
  real-world assertion.

### 12.2 Security

- Direct policy-override, roleplay, encoded, multilingual, and multi-turn
  injection corpus does not reveal secrets or change permanent boundaries.
- Malicious instructions inside a stored source are treated as quoted data.
- Session A cannot read, append, stream, or delete session B.
- Model-authored HTML, image, executable link, and malformed Markdown do not
  become active browser content.
- Oversized input, repeated turns, concurrent turns, reconnect storms, and duplicate
  requests remain within configured token, worker, and cost bounds.
- Provider and database failures expose only safe error codes and preserve
  earlier validated content.
- Logs contain no secret or full conversation payload.

### 12.3 Safety and interpretation

- No output induces a financial or market action.
- No output states an unsupported future result or relationship explanation.
- User assumptions never appear as accepted current facts.
- Scenario labels and caution remain visible on every assistant response.
- Data-bearing responses retain data-as-of timing.
- Individual participant data never enters the model bundle or public API.

### 12.4 Operations

- Per-turn token, latency, rejection reason, and estimated cost are observable
  without logging full content.
- Stop switch, rate limits, timeout, retry, queue depth, and total daily budget
  have deterministic tests.
- Expired sessions become unavailable according to the approved retention
  policy.
- The previous accepted v8 briefing remains available through rollback.

## 13. Required approvals

The following approvals are independent; approving the plan approves none of
the mutations below:

1. Phase 2 scope entry and the proposed summary/scenario wording policy.
2. Public API request, response, streaming, and error contract.
3. Append-only schema migration plus retention/deletion behavior.
4. Any new dependency or external state store.
5. Provider, model, per-turn limits, evaluation count, and budget.
6. Infrastructure, worker topology, rate-limit store, CORS, or hosting change.
7. Applying a migration to a named local/development database.
8. Deployment or any production write.
9. Final activation and supersession of active v8.

## 14. Rollout and rollback

1. Build behind a disabled feature flag with fixture-only tests.
2. Run deterministic security and content corpora without a provider.
3. After explicit approval, apply any migration only to the named local
   development database.
4. After separate provider approval, run a bounded evaluation over selected
   zero-source, source-backed, stale, thin-data, and adversarial cases.
5. Review actual browser output, latency, cost, rejection rate, and session
   isolation.
6. Accept, revise, or reject the new path. Do not activate by implementation
   completion alone.
7. If activated later, keep v8 read compatibility and a feature-flag rollback
   until the new contract has an agreed observation period.

Rollback disables new summary/chat generation, stops workers, rejects new
session creation, and continues serving the previous valid briefing. It must
not require deletion or mutation of accepted report history.

## 15. Open decisions

1. Is the chat a fifth detail tab or a section inside the current briefing tab?
2. Is 24-hour anonymous retention acceptable, or should the initial release be
   session-only with immediate expiry when the browser session ends?
3. Does a user receive an explicit delete control in the first release?
4. Which allow-list Markdown features are necessary beyond paragraphs, lists,
   and emphasis?
5. Should the chat use the same provider/model as the summary or an isolated
   configuration with a separate budget?
6. What exact input/output/turn/rate limits meet the desired experience?
7. Does the initial release permit accepted stored sources only, or also a
   separately refreshed server-side source bundle before session creation?
8. What quality threshold and observation period permit v8 supersession?

## 16. PM stance

Proceed only with TASK-124 and TASK-125 first. They can lock product language,
assumption semantics, retention, threat boundaries, and approval packets
without changing runtime state. Do not start schema, provider, or UI work until
those two reviews close.

The smallest responsible prototype is tool-free, issue-scoped, anonymous,
short-lived, limited to ten turns, and rendered through a restricted Markdown
subset. This provides the intended conversational freedom while keeping model
authority and data exposure narrow.
