<!--
Purpose:        Project-specific terms, abbreviations, and the binding wording policy
Owner:          PM / Planner (owns wording policy), all agents (contribute terms)
Update Trigger: New domain term introduced, wording policy changed
Harness Version: 1.1
-->

# Glossary — Outlook Signals

_Last updated: 2026-07-10_

## Domain Terms (use these exact framings in UI copy and AI output)

| Term | Definition |
|------|-----------|
| Reflected expectation value | The current price/probability from Polymarket, reframed as "expectation reflected in market data," never "probability of the outcome" |
| Interpretation-caution badge | Visual indicator (not a "trust badge") shown when activity level, liquidity, or volatility make a metric unreliable to over-interpret |
| Related event candidate | A manually curated (3–5 issues only) contextual event shown alongside a market's change — always "candidate," never asserted as "cause" |
| Heat score | Composite ranking metric (attention + volatility + magnitude of change) that powers the home dashboard "top movers" ranking |
| Expectation Shift Detected | The MVP's only sudden-change signal: ±5pp change within a rolling window (Service Design §7) |
| Data-as-of timestamp | Required on every data-bearing screen; shown even when serving last-known-good/fallback data |
| Confidence / caution level | `sufficient` / `caution_low_activity` / `caution_high_volatility` / `insufficient_data` — DB field `confidence_level` |
| v3 AI report | The ADR-032 report shape for `/api/issues/{id}/report`: fixed fields only, no free-form analysis, no causal or action-oriented wording, and storage allowed only after schema plus copy-safety validation |
| Context candidate note | Optional v3 report field derived only from manually curated related-event candidates; always framed as context to check alongside the observed change, never as a cause |
| Offline candidate discovery | A non-public PM/Data review aid that may help find possible context candidates but cannot write to the database, change the public API, display results, or replace manual curation in MVP/v3 |

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

### Prohibited wording — never ship, in any context (UI, AI output, error states, placeholder text, internal debug labels)

`bet, buy, sell, trade, position, long, short, profit, win rate, odds, copy trader, follow this user, expert trader, best pick, recommended outcome, high-return opportunity, guaranteed prediction, signal to act, recommendation`

Korean v3 additions for UI, fallback strings, and AI/template output:

`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 추천, 보장, 확정, 따라하기, 고수, 전문 트레이더, 고수익, 기회`

Policy/lint documents and tests may quote prohibited expressions only to define
or verify the blocking rule.

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

### v3 report wording replacements (ADR-032)

| Avoid | Use instead |
|---|---|
| Automated news match | Manually curated context candidate |
| Cause of the movement | Context candidate around the observed change |
| Outcome is likely | Current public data reading |
| AI prediction | Data summary / issue report |
| Confidence in the outcome | Data reliability / interpretation caution |
