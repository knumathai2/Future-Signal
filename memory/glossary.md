<!--
Purpose:        Project-specific terms, abbreviations, and the binding wording policy
Owner:          PM / Planner (owns wording policy), all agents (contribute terms)
Update Trigger: New domain term introduced, wording policy changed
Harness Version: 1.1
-->

# Glossary — Outlook AI Signals

_Last updated: 2026-07-12_

## Domain Terms (use these exact framings in UI copy and AI output)

| Term                        | Definition                                                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Reflected expectation value | The current Polymarket value, framed as an expectation reflected in market data rather than a real-world result probability                                               |
| Interpretation caution      | Required text or badge that limits over-interpretation of thin, volatile, stale, or incomplete data                                                                       |
| Data-as-of timestamp        | Required timestamp on every data-bearing screen, including fallback and last-known-good states                                                                            |
| Confidence / caution level  | `sufficient`, `caution_low_activity`, `caution_high_volatility`, or `insufficient_data`                                                                                   |
| Heat score                  | Ranking metric used to order notable issue changes; never an action recommendation                                                                                        |
| Expectation Shift Detected  | The implemented ±5 percentage-point observed-change marker                                                                                                                |
| Verified context            | Public-source material accepted only after deterministic provenance, relevance, timing, supported-claim, duplicate, contradiction, and attribution checks                 |
| V8 issue-centered briefing  | Evidence-bounded headline, summary, and typed sections covering current situation, recent change, interpretation, conditions, later information, and optional limitations |
| Current summary             | The stable v8 briefing surface for exact definitions, stored observations, accepted material, timing, limitations, and caution                                            |
| Scenario conversation       | A separate issue-scoped conditional exploration surface that cannot promote an assumption to a current fact                                                               |
| Premise class               | Server-owned scenario state: `confirmed_fact`, `stored_observation`, `user_assumption`, `model_scenario`, or `unverified_context`                                         |
| Fail closed                 | Withhold content whenever provenance, evidence, schema, timing, numeric, leakage, wording, or rendering validation is missing or inconsistent                             |

## Abbreviations

| Abbr | Full Form                    | Description                                      |
| ---- | ---------------------------- | ------------------------------------------------ |
| ADR  | Architecture Decision Record | Log of technical decisions (`decisions.md`)      |
| MVP  | Minimum Viable Product       | The 5-day hackathon build scope (PRD §6)         |
| pp   | Percentage points            | Unit for all change metrics (never "%")          |
| Gate | Human Approval Gate          | Checkpoint requiring user approval (`AGENTS.md`) |

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

### Briefing and scenario policy

The product keeps the evidence-bounded current briefing separate from a freer
conditional scenario conversation without changing the permanent boundary.

- Current-summary exact values, dates, definitions, source identities, and
  current external facts remain blocking and reconstructible.
- Ordinary explanation, organization, section count, and zero-source coverage
  are quality diagnostics unless they create a current factual claim.
- Scenario answers may explore user assumptions, generic counter-cases,
  distinguishing variables, and information that would change an assessment.
- Every assumption remains visibly conditional and keeps its server-owned
  premise class across turns.
- A scenario may explore a relationship only as a hypothesis; it cannot state
  that external material explains observed movement.
- The existing hard blocks, contextual-expression rules, privacy boundary,
  aggregate-only participant policy, data timing, and interpretation caution
  remain unchanged.
- Application feature flags default to disabled; the production Compose
  profile enables the scenario API and workers explicitly.

### Use-carefully wording — only with a qualifying phrase attached, never standalone

| Word              | Safe pattern                                                                                         |
| ----------------- | ---------------------------------------------------------------------------------------------------- |
| Signal            | Always as a full compound phrase: "[Neutral noun] Signal Detected"                                   |
| Alert             | Prefer "notify" over "alert" entirely; if used, only as a user-configured notification category name |
| Watch             | Only as "watchlist"/"monitor" noun forms, never "watch this one closely"                             |
| Momentum          | Always paired with "score" + a one-line definition                                                   |
| Confidence        | Rename to "Data reliability" wherever possible; never adjacent to the probability number itself      |
| Market activity   | Only as a neutral descriptor ("Trading activity: [level]"), never implying an outcome                |
| Probability spike | Only as a defined, labeled signal name, never as a headline/notification hook                        |

### Prohibited-vs-replacement quick reference (PRD §3.4)

| Avoid                        | Use instead                                              |
| ---------------------------- | -------------------------------------------------------- |
| We predict the future        | We show how expectations are changing                    |
| The likelihood has increased | The reflected expectation value has risen in public data |
| Here's what people think     | Change observed in Polymarket participant data           |
| Investment signal            | Issue-change observation indicator                       |
| Recommended issue            | Exploration list ranked by change magnitude              |
| Trust badge                  | Interpretation-caution badge                             |
| Cause analysis               | Related event candidate                                  |
