# Service Design: Data, Metrics, AI & Signal Layer for Outlook AI Signals

Document version: v1.0
Date: 2026-07-07
Companion to: [PRD](../prd/README.md) (Outlook AI Signals — 5-day hackathon PRD, v1.1)
Purpose: Define the Polymarket data collection plan, analysis metrics, AI I/O contract, sudden-change signal rules, and participant-analysis policy that underlie the product. Written to convert directly into engineering tickets and a Phase-2 PRD.

Assumption: this document does not replace PRD. Where the hackathon PRD already made a decision (binary markets only, 30–50 markets, template-first summaries, no auto context matching, no accounts), this document treats that as a hard constraint for the frozen v3 MVP. ADR-038 is the narrow post-MVP exception for TASK-056~065.

---

## 1. Service Design Summary

Outlook AI Signals turns Polymarket's public order-book and market metadata into a **neutral issue-monitoring layer**: what changed, by how much, how fast, and how much confidence the underlying data supports. It is not a forecasting tool, not a trading dashboard, and not a leaderboard of participants.

Three design commitments run through every section below:

1. **Price is "expectation reflected in the market," never "probability of the future."** All copy, metrics, and AI output must use "expectation value / probability reflected in public prediction-market data" language, never "chance this will happen."
2. **Every number ships with a caution signal.** Low liquidity, low volume, short history, or high volatility must visibly qualify any metric before a user can misread it as strong signal.
3. **Aggregation over identification.** Participant-level and wallet-level data may only be used in aggregate. No feature may let a user find, follow, rank, or predict an individual participant.

The rest of this document assumes the hackathon's technical constraints (binary markets, 30–50 active markets, batch/manual refresh) but designs the data model and metric logic to extend cleanly to a larger, always-on Phase 2 product.

---

## 2. Polymarket Data Collection Plan

Polymarket exposes data through two practical surfaces: the **Gamma API** (market/event metadata, descriptions, categories, volume, liquidity, end dates) and the **CLOB API** (order book, trade prices, `prices-history` time series per token). A separate **Data API / subgraph** exposes trade and activity records, which is where wallet-level detail lives — this is the surface that needs the most policy care (see Section 8).

| Data type | Why needed | Contribution to issue analysis | MVP status | Limitations / risks |
|---|---|---|---|---|
| Market title (`question`) | Primary label shown to users | Core identity of the issue | **Must-have** | Titles are sometimes jargon-heavy or ambiguous out of context |
| Market category / tags | Grouping, filtering, category-level comparison | Lets users scan by domain (politics, economy, tech) | **Must-have** (fallback: manual mapping if source tags are messy) | Polymarket tagging is inconsistent across markets; may need manual normalization for the 30–50 market MVP set |
| Market description | Context for unfamiliar issues | Reduces need for users to leave the product to understand what's being asked | **Must-have** | Descriptions can be terse or written in trader shorthand, not general-audience language |
| Outcome options (Yes/No, or multi-outcome list) | Defines what "the price" means | Required to interpret any probability number correctly | **Must-have** for binary; multi-outcome deferred | Multi-outcome markets (N options) don't reduce to a single probability line — real complexity, correctly excluded from MVP per PRD |
| Current probability / price | The headline number | Anchor for all change metrics | **Must-have** | A price is a market-clearing number, not a calibrated forecast — must always be labeled "reflected expectation," not "probability of outcome" |
| Historical probability (price) time series | Powers the chart, change %, inflection points | The core visual proof of "expectation is shifting" | **Must-have** | `prices-history` resolution and retention vary by market age/activity; thin markets have gappy history |
| Trading volume (total, 24h) | Distinguishes real movement from noise on a dead market | Required input for every caution badge and for the attention/heat metrics | **Must-have** | Volume denominated in USDC notional, not "number of people" — must not be presented as participation count |
| Liquidity (order book depth) | A market with a big price move but no depth is unreliable | Core input to the "interpretation caution" badge | **Must-have** | Liquidity can be added/pulled by a single market maker; not a stable measure of interest |
| Open interest | Would help judge how "real" a position shift is | Nice conceptual fit, but Polymarket doesn't expose a clean open-interest figure the way futures markets do — would need to be derived indirectly from token supply/holdings | **Nice-to-have** (likely infeasible for MVP) | High implementation cost for ambiguous value; do not block MVP on this |
| Market creation date | Needed to compute market age and to contextualize "7-day change" when a market is <7 days old | Prevents mislabeling a brand-new market's full history as a "sudden change" | **Must-have** | — |
| Market end date / resolution date | Tells users how much runway is left, matters for interpreting volatility near resolution | Markets naturally get noisier and more volatile near resolution — must be visible so users don't overread late-stage swings | **Must-have** | — |
| Market status (active/closed/resolved) | Filtering; must exclude resolved markets from "issue is still evolving" framing | Keeps the monitoring list to live, undecided issues | **Must-have** | — |
| Recent activity (trade count, last trade time) | Freshness check; distinguishes "actively traded" from "stale price sitting there" | Input to attention/heat metrics and staleness warnings | **Must-have** | — |
| Number of participants (unique wallets) | Rough proxy for breadth of engagement, useful only in aggregate | Supports "engagement is broad vs. concentrated" framing at the market level | **Nice-to-have** | Wallets ≠ people (one person can run many wallets); must be shown as "unique addresses," not "number of participants," and never drilled into individual wallets in MVP |
| Comments / public discussion data | Could add qualitative context | Low value relative to cost/risk for MVP; Polymarket's comment surface is a secondary feature with unclear API stability and its own moderation/attribution issues | **Excluded from MVP** | Attribution, moderation, and ToS risk outweigh benefit; revisit only if a clear, permitted read-only API exists and a moderation plan is built |

### Data source note
No user accounts, positions, or personal identifiers should ever be collected. All collection is of public, already-aggregated market data (or public wallet-tagged trade data used only in aggregate — see Section 8). This keeps the service outside of any KYC/financial-data handling obligations, since it does not process user funds, accounts, or personal trading activity.

---

## 3. MVP Data Scope

Must-have, in build order:

1. Market id, title, description, category/tag, outcome set (binary only)
2. Current price, price history (with enough resolution for 24h/7d deltas and a readable chart)
3. 24h and 7d volume
4. Liquidity (current snapshot at minimum; history is a stretch goal)
5. Creation date, end date, status (active/closed)
6. Last trade timestamp / recent activity flag
7. Data-as-of timestamp attached to every payload (required for the disclaimer pattern already defined in PRD §8.10)

This set is sufficient to power: the dashboard ranking, the detail chart, the change-% metrics, and the interpretation-caution badges — i.e., everything marked P0 in PRD §6.3.

---

## 4. Excluded Data Scope

Explicitly out of MVP, with reasoning:

| Excluded data | Reason |
|---|---|
| Comments / discussion threads | Attribution, moderation, and API-stability risk; low analytical value relative to cost |
| Wallet-level trade history / individual positions | Core ethical boundary of this product (Section 8); also legally sensitive if it drifts toward "trading signal" territory |
| Open interest | Not cleanly exposed by Polymarket; not worth custom derivation for MVP |
| Multi-outcome markets | Doesn't reduce to a single change-% line; adds a whole second UI/metric model for a hackathon timeline |
| Unverified, source-less, or causal external event matching | Excluded. The only automated exception is ADR-038's citation-backed, independently verified, fail-closed v4 context-candidate path. |
| Any personally identifying data about traders | Out of scope entirely — the product analyzes markets, not people |

---

## 5. Core Analysis Metrics

All metrics are framed as **issue-monitoring indicators**, not trading signals. None should ever be described with words like "buy," "signal to act," "opportunity," or "edge." Each metric below states its required data footprint against Section 3, so you can see immediately which are buildable in 5 days vs. which need Phase 2 data (volume history, liquidity history, cross-market data).

| Metric | Definition | Input data | Calc logic | User value | MVP priority | Visualization | Misinterpretation risk |
|---|---|---|---|---|---|---|---|
| Probability change rate | Δ in reflected price over a window, in percentage points | Price history | `price(t) - price(t-window)` | Core "what changed" number | **P0** | Signed %p with color + arrow | Easily read as "likelihood went up," must be labeled "expectation reflected in market" |
| 24h probability movement | Change rate over 24h | Price history | Same as above, window=24h | Short-term monitoring | **P0** | Card badge, chart marker | Can overweight a single large trade in a thin market |
| 7d probability movement | Change rate over 7d | Price history | Same as above, window=7d | Medium-term trend | **P0** | Card badge, chart line | New markets (<7d old) need "insufficient history" flag instead of a number |
| Volatility score | Dispersion of price changes over a window (e.g. stdev of hourly Δ over 7d) | Price history | Standard deviation of returns | Distinguishes "steadily reassessed" from "whipsawing" issues | **P1** | Small icon/gauge next to chart | Could be read as "riskier bet" — must stay framed as "how unsettled is public expectation" |
| Momentum score | Whether recent change direction is continuing or reversing (e.g. compare last 24h Δ direction/magnitude vs prior 24h) | Price history | Directional consistency over 2 consecutive windows | Flags issues in an active reassessment, not just a one-off jump | **P1** | Directional arrow strength indicator | Closest metric to "trend continuation," must not be phrased as "likely to keep moving this way" |
| Attention score | Composite of recent volume + trade count + recency of activity | Volume, trade count, last-trade time | Weighted normalization of the three, relative to the market's own baseline | Separates "actually being reassessed" from "stale price nobody is trading" | **P1** | Small flame/heat icon, tiered (low/med/high) | Could look like "popularity ranking of a bet" — keep as "engagement level," never "hot pick" |
| Volume spike score | Recent volume vs. trailing baseline volume | Volume history | `current_window_volume / rolling_avg_volume` | Detects unusual engagement independent of price movement | **P1** (needs volume history, not just snapshot) | Badge on card + annotation on chart | Could be misread as "smart money moving in"; keep strictly descriptive |
| Liquidity change | Δ in order-book depth over a window | Liquidity snapshots over time | `liquidity(t) - liquidity(t-window)` | Helps judge whether a price move is backed by real depth or a thin book | **P2** (needs liquidity history pipeline) | Caution-badge input, not shown as standalone number initially | Users may confuse "liquidity" with "conviction" |
| Market confidence score | How much the *current* price should be trusted as a stable reading (composite of liquidity + volume + market age) | Liquidity, volume, age | Weighted composite, normalized 0–100 or low/med/high | Single glance answer to "how much should I trust this number" | **P0** as a simplified version (this is essentially the existing "interpretation caution badge" in PRD §8.7, generalized into a score) | Badge, not a raw number | Naming risk: "confidence" sounds like "confidence this will happen" — must be relabeled as "data reliability" in UI copy, never shown next to the probability number itself |
| Uncertainty score | Inverse framing of confidence — how wide/unsettled the market's view currently is | Volatility, spread (bid-ask), liquidity | Composite, higher = more unsettled | Helps users avoid overreading a noisy market | **P1** | Badge / qualitative label (Low/Medium/High uncertainty) | Do not let this collapse into "50/50 = most uncertain" oversimplification — uncertainty is about stability of the read, not proximity to 50% |
| Issue heat score | Composite ranking metric combining attention + volatility + magnitude of recent change | Attention score, volatility, change rate | Weighted composite for the "top movers" ranking | Powers the home dashboard ranking (PRD §8.1–8.2) | **P0** (can start as a simple weighted rank of |Δ24h| + volume-adjusted, don't need full composite v1) | Ranked list, home dashboard | Must not be styled as "top picks" — rank explicitly by "expectation change," and reflect it in the label ("today's most reassessed issues") |
| Sudden change signal | See Section 7 | Change rate, volume, volatility | Threshold-based | Flags where to look first | **P0** (simple threshold version) | Marker on chart + badge on card | See Section 7 |
| Narrative shift score | Detects a *sustained reversal* in direction (not just a spike) — e.g., 3+ consecutive periods moving against the prior trend | Price history | Directional-run detection | Distinguishes "one-off news spike that reverted" from "actual reassessment that stuck" | **P2** (needs more history + tuning than a hackathon allows) | Annotated chart segment | Highest risk of sounding like "trend reversal = trade signal"; keep purely descriptive ("expectation direction changed and held") |

### MVP metric set (buildable in 5 days from Section 3 data)
Probability change rate, 24h movement, 7d movement, a simplified issue heat rank, and a simplified confidence/caution badge (already scoped as P0 in PRD). This matches the hackathon PRD almost exactly — the additions here (attention, volatility, momentum) are P1 stretch goals if time allows, and volume-spike/liquidity-change/narrative-shift are Phase 2 once historical volume/liquidity pipelines exist.

---
