<!--
Purpose:        Project-specific terms, abbreviations, and the binding wording policy
Owner:          PM / Planner (owns wording policy), all agents (contribute terms)
Update Trigger: New domain term introduced, wording policy changed
Harness Version: 1.1
-->

# Glossary — Outlook AI Signals

_Last updated: 2026-07-12_

## Domain Terms (use these exact framings in UI copy and AI output)

| Term | Definition |
|------|-----------|
| Reflected expectation value | The current price/probability from Polymarket, reframed as "expectation reflected in market data," never "probability of the outcome" |
| Interpretation-caution badge | Visual indicator (not a "trust badge") shown when activity level, liquidity, or volatility make a metric unreliable to over-interpret |
| Related event candidate | The frozen v3 term for a manually curated contextual event shown alongside a market's change — always "candidate," never asserted as "cause" |
| Heat score | Composite ranking metric (attention + volatility + magnitude of change) that powers the home dashboard "top movers" ranking |
| Expectation Shift Detected | The MVP's only sudden-change signal: ±5pp change within a rolling window (Service Design §7) |
| Data-as-of timestamp | Required on every data-bearing screen; shown even when serving last-known-good/fallback data |
| Confidence / caution level | `sufficient` / `caution_low_activity` / `caution_high_volatility` / `insufficient_data` — DB field `confidence_level` |
| v3 AI report | The ADR-033 eight-field report shape for `/api/issues/{id}/report`: fixed fields only, no open-ended analysis, no causal or action-oriented wording, and storage allowed only after schema plus copy-safety validation |
| External context | Nullable v3 narrative derived only from PM/Data-approved related-event notes; source metadata remains in issue-detail `related_events`, and the section is hidden only when the value is `null` |
| Context candidate comparison | Required v3 `possible_drivers` content derived only from approved candidate title/date or the fixed absence copy; always states that the data does not establish a relationship with the observed movement |
| Offline candidate discovery | A non-public PM/Data review aid that may help find possible context candidates but cannot write to the database, change the public API, display results, or replace manual curation in MVP/v3 |
| Verified context candidate | A v4 candidate backed only by OpenRouter `url_citation` annotations and accepted by deterministic hard gates plus an independent verifier model; timing may be compared with a change episode, but no relationship is asserted |
| Change episode | A v4 display unit connecting one observed metric interval, its metric evidence ID, any verified context-candidate IDs, source metadata, timing, and interpretation caution |
| v4 evidence-grounded report | The TASK-056 seven-field structured report with metric/candidate evidence references; it excludes legacy v1-v3 rows, rejects unsupported values or context, and uses `context_summary=null` when no verified candidate exists |
| Fail closed | Withhold a candidate or report from the public API whenever citation provenance, hard-gate verification, independent verification, evidence references, schema, timing, or safety validation is missing or inconsistent |
| v8 issue-centered briefing | The TASK-112 report shape that preserves v7 evidence/source controls while organizing the narrative around current situation, recent change, interpretation, key conditions, later information, and optional limitations. |
| v8 source-level-2 context | The TASK-113 retrieval policy that uses a bounded 90/180-day horizon and deterministic aliases while keeping every public claim tied to an exact accepted annotation excerpt and visible A-C source attribution. |
| Current summary | The TASK-124 next-contract surface for issue definition, exact stored observations, accepted current material, timing, and limitations. Ordinary safe prose may be flexible; exact data and current facts remain reconstructible. Active v8 remains public until TASK-131 acceptance. |
| Scenario conversation | The TASK-124 free-form, issue-scoped conditional exploration surface. It has no required visible section template and cannot promote an assumption to a current fact. |
| Premise class | Server-owned scenario state: `confirmed_fact`, `stored_observation`, `user_assumption`, `model_scenario`, or `unverified_context`. The model may discuss but never change a class. |

## Abbreviations

| Abbr | Full Form | Description |
|------|-----------|-------------|
| ADR | Architecture Decision Record | Log of technical decisions (`decisions.md`) |
| MVP | Minimum Viable Product | The 5-day hackathon build scope (PRD §6) |
| pp | Percentage points | Unit for all change metrics (never "%") |
| Gate | Human Approval Gate | Checkpoint requiring user approval (`AGENTS.md`) |

## Harness Terms

| Term | Definition |
|------|-----------|
| Harness | This full AI development OS document structure |
| Session | A single agent work unit |
| Active Task | A task currently in `tasks/active.md` |
| Registry | The list of active agent roles (`AGENTS.md`) |

---

## Wording Policy (binding — see `../standards.md` Content Safety Lint for enforcement)

### Hard-block wording — never ship, in any context (UI, AI output, error states, placeholder text, internal debug labels)

`bet, buy, sell, trade, position, long, short, profit, win rate, odds, copy trader, follow this user, expert trader, best pick, recommended outcome, high-return opportunity, guaranteed, guaranteed prediction, signal to act, recommend, recommendation`

Korean hard blocks for active v8:

`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 따라하기, 고수, 전문 트레이더, 고수익`

### Contextual wording — active v8 only

`확정, 보장, 추천, 기회, 전망, 원인`

These expressions are not approved merely because evidence is present.
Source-free use is limited to explicit negation/limitation or a verification
inquiry such as `확정 여부`. A positive use requires an exact same-section
`source:*` reference, a stored supported-claim marker of equal strength, and
visible attribution in the authored sentence. Headline/summary may use only
the source-free safe forms. Ambiguous uses fail closed. V1-v7 retain the
historical flat block.

Policy/lint documents and tests may quote prohibited expressions only to define
or verify the blocking rule.

### Approved next-contract summary and scenario policy

TASK-124 permits a more natural current summary and a substantially freer
scenario conversation without changing the permanent product boundary.

- Current-summary exact values, dates, definitions, source identities, and
  current external facts remain blocking and reconstructible.
- Ordinary explanation, organization, section count, and zero-source coverage
  are quality diagnostics unless they create a current factual claim.
- Scenario answers may explore user assumptions, generic counter-cases,
  distinguishing variables, and information that would change an assessment.
- Every assumption remains visibly conditional and keeps its server-owned
  premise class across turns and conversation compaction.
- A scenario may explore a relationship only as a hypothesis; it cannot state
  that external material explains observed movement.
- The existing hard blocks, contextual-expression rules, privacy boundary,
  aggregate-only participant policy, data timing, and interpretation caution
  remain unchanged.
- Active v8 remains the runtime policy until TASK-131 records an activation
  decision for a newly versioned contract.

### Use-carefully wording — only with a qualifying phrase attached, never standalone

| Word | Safe pattern |
|---|---|
| Signal | Always as a full compound phrase: "[Neutral noun] Signal Detected" |
| Alert | Prefer "notify" over "alert" entirely; if used, only as a user-configured notification category name |
| Watch | Only as "watchlist"/"monitor" noun forms, never "watch this one closely" |
| Momentum | Always paired with "score" + a one-line definition |
| Confidence | Rename to "Data reliability" wherever possible; never adjacent to the probability number itself |
| Market activity | Only as a neutral descriptor ("Trading activity: [level]"), never implying an outcome |
| Probability spike | Only as a defined, labeled signal name, never as a headline/notification hook |

### Prohibited-vs-replacement quick reference (PRD §3.4)

| Avoid | Use instead |
|---|---|
| We predict the future | We show how expectations are changing |
| The likelihood has increased | The reflected expectation value has risen in public data |
| Here's what people think | Change observed in Polymarket participant data |
| Investment signal | Issue-change observation indicator |
| Recommended issue | Exploration list ranked by change magnitude |
| Trust badge | Interpretation-caution badge |
| Cause analysis | Related event candidate |

### v3 report wording replacements (ADR-033)

| Avoid | Use instead |
|---|---|
| Automated news match | Manually curated context candidate |
| Cause of the movement | Context candidate around the observed change |
| Outcome is likely | Current public data reading |
| AI prediction | Data summary / issue report |
| Confidence in the outcome | Data reliability / interpretation caution |

### v4 automated-context wording replacements (ADR-038)

| Avoid | Use instead |
|---|---|
| Automated news match | Verified context candidate for the change episode |
| Event that moved the value | Public information recorded in the same review window |
| Proof of the result | Source-supported context that does not establish the real-world result |
| No event found | Hide the context section and keep `context_summary=null` |
