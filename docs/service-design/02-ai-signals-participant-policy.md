# Service Design: AI I/O, Sudden Signals, Participant Policy

_Source: former project-root Service Design sections 6-8._

---

## 6. AI Input / Output Design

**Design decision consistent with PRD §8.8: the default AI is a template-filling engine over computed metrics, not a free-form LLM analyst.** An LLM may be used only to smooth the phrasing of a template-constrained output — never to generate open-ended interpretation, causal claims, or predictions. This is both a safety constraint and a scope constraint: free-form LLM analysis was explicitly deferred in the hackathon PRD (§6.5) pending a proper evaluation/guardrail framework.

### Active v8 inputs

- Exact market definition revision and tracked outcome
- Generation-time metric and closest eligible snapshot
- Fixed 24-hour and 7-day observed changes when available
- Bounded observed-history summary and data limitations
- Accepted context, source, and supported-claim records
- Data, context, and generation timestamps
- Opaque evidence references plus prompt, policy, and input-schema versions

The writer receives a frozen, typed evidence bundle. It does not receive
unbounded browsing output or permission to create identifiers, source metadata,
metrics, dates, or URLs.

### Active v8 outputs

- One issue-centered headline
- One two-to-four sentence summary
- Two-to-six uniquely typed sections
- Paragraph or bullet presentation with exact evidence references
- Zero or more exact stored A-C sources
- Deterministic cache state, limitations, caution, and timing

Required sections are `current_situation` and `recent_change`. Optional
sections are `interpretation`, `key_conditions`, `what_to_watch`, and one
`limitations` section.

### Permanent constraints

- Every factual authored section must reconstruct from supplied evidence.
- The writer cannot create or alter metrics, identifiers, source metadata,
  supported claims, timestamps, or links.
- External material cannot be presented as the explanation for an observed
  movement.
- Missing evidence produces an explicit zero-source or limitation state.
- The current prohibited-language policy remains in `standards.md` and
  `memory/glossary.md`; generation and read-time validation share it.
- Every full report retains data-as-of timing and interpretation caution.
- Provider or validation failure preserves the previous valid report.

### Historical contracts

V1-v7 shapes and their supersession records are historical. Their concise map
is in `docs/archive/ai-report-contracts/README.md`; accepted decisions remain
in `memory/decisions.md`, and detailed artifacts remain recoverable from Git
history.

### 6.12 Approved v8 issue-centered narrative contract

TASK-112 keeps v7's evidence and source safety boundary but organizes authored
content around the questions a general reader asks: what the issue is, what is
currently confirmed, what changed recently, what the available material can
and cannot support, which conditions matter, and what information would change
the assessment. Numeric observations support that narrative instead of leading
it. External context is integrated only where accepted source evidence supports
it, and a limitations section may appear at most once.

Every section still carries exact opaque evidence references. Source references
still require their context parent, authored links remain blocked, prohibited
language remains blocked, and the writer cannot infer a background for an
observed change. V1-v7 rows remain append-only audit history.

### 6.13 Approved v8 source-retrieval refinement

TASK-113 keeps the v8 publication blockers but widens discovery before those
blockers run. Research uses a deterministic 90-day or 180-day issue horizon,
adds bounded cross-wording queries for common entity and issue concepts, and
tests relevance across the source title plus exact annotation excerpt. If the
source is relevant but its excerpt does not support the provider's broader
candidate wording, the exact excerpt becomes the supported claim instead.

Only OpenRouter `url_citation` annotations with safe URLs, a visible publisher
domain and title, and a non-empty excerpt can enter classification. A-C source
levels, source-parent linkage, blocked domains, duplicate/conflict handling,
conditional verification, attribution, and the prohibition on inferred
relationships with an observed movement remain unchanged. The active context
policy fingerprint is `v8-source-level-2`.
If a successful server-tool response contains exact citation annotations but
not the requested JSON body, v8 ignores body links and creates narrow
annotation-only candidates from the citation title, URL, and excerpt before
running the same relevance and publication gates.

### 6.14 Active-v8 contextual wording policy (TASK-116)

Active v8 no longer treats every Korean occurrence of `확정`, `보장`, `추천`,
`기회`, `전망`, and `원인` as equivalent. Explicit negation, limitation, and
verification-inquiry uses may pass without source evidence. A positive use is
allowed only inside a section that references an accepted source whose stored
supported claim contains an approved same-strength marker, and only when the
authored sentence visibly attributes the statement to that source or
institution. Unsupported, ambiguous, predictive, outcome-asserting, and
action-inducing uses fail closed.

Financial/action wording remains an unconditional block. Headline and summary
have no section evidence scope and therefore may use only source-free safe
forms. The same classifier runs before storage and during API reconstruction;
v1-v7 retain their historical flat filters.

### 6.15 Validated-block streaming contract (TASK-117)

V8 may deliver a briefing progressively only at complete template-block
boundaries. One provider request emits NDJSON in this order: one
`headline_summary` object, two-to-six consecutively indexed `section` objects,
and one `complete` object. Arbitrary token chunks are never public output.

Before a block is persisted or delivered, the backend validates its exact
shape, section order and uniqueness, evidence references, source-parent links,
authored URLs, contextual wording, and all retained future/relationship and
financial/action language gates. The final object reruns the full-report
validator and required-section checks. A failed block is never persisted; any
earlier individually valid blocks from that attempt remain audit-only and the
Frontend removes them when the request fails. The previous complete valid
briefing remains the last-known-good public fallback.

### 6.16 Approved next-contract summary and scenario policy (TASK-124)

TASK-124 separates the future AI experience into a current summary and an
issue-scoped scenario conversation. It is an approved policy design, not an
active-v8 replacement.

The current summary may use a flexible narrative order, omit unhelpful
sections, and remain useful with definition plus metric evidence when no
accepted external source exists. Exact values, dates, units, definitions,
source identities, current external facts, timing, limitations, and caution
remain blocking and reconstructible. Ordinary safe explanation and preferred
organization become diagnostics rather than whole-report blockers.

The scenario conversation has no required visible content template. It may
explore user assumptions, generic counter-cases, variables, and information
that would change an assessment. The server owns premise classes for confirmed
facts, stored observations, user assumptions, model scenarios, and unverified
context. The model cannot promote a premise. Permanent financial/action,
real-world-result, unsupported-relationship, privacy, individual-participant,
secret-leakage, and unsafe-rendering rules remain blocking.

The first implementation remains issue-scoped, anonymous, short-lived,
tool-free, and unable to browse, query the database, execute code, open user
URLs, or perform external actions. TASK-125 owns the threat, retention, API,
and storage proposal. TASK-129 implements the separate default-off Frontend
without changing the active-v8 contract. TASK-131 must record a separate
activation decision.

---

## 7. Sudden Change Signal Design

Signals answer "where should a monitoring user look first," not "what should you do." All labels below intentionally avoid trading-alert vocabulary.

| Signal name (user-facing) | Trigger condition | Required data | Example threshold | Severity | False-positive risk | Display | MVP? |
|---|---|---|---|---|---|---|---|
| Probability Movement | Any nonzero Δ over the selected window | Price history | N/A (always shown as the base metric) | — (this is the metric, not a signal) | — | Number/arrow on card | **Yes** — this is the P0 change-% metric |
| Expectation Shift Detected | |Δ| exceeds a short-window threshold | Price history | ±5 pp within a rolling window (matches PRD §8.6 inflection-point threshold) | Medium | High in thin markets — a single trade can move price 5pp on low liquidity | Marker on chart + badge on card | **Yes** (already scoped in PRD as the inflection-point marker) |
| Attention Spike | Recent volume or trade count well above the market's own trailing baseline | Volume/trade-count history | e.g. 24h volume > 3x trailing 7-day daily average | Medium–High depending on magnitude | Baseline is noisy for low-volume markets; needs a minimum-volume floor to avoid false spikes on near-dead markets | Badge, separate from price-change badge | **P1** (needs volume history pipeline) |
| Issue Reassessment Signal | Sustained directional movement across multiple consecutive windows (not just one spike) | Price history | e.g. same-direction Δ in 3 consecutive 24h windows, cumulative ≥ 10pp | High | Can still be a slow drift rather than a "reassessment" — label carefully | Chart segment highlight | **P1–P2** |
| Unusual Market Activity | Combination trigger: volatility increase + attention spike occurring together | Price history, volume history | e.g. volatility > 2x its own 30-day baseline AND volume spike also triggered | Critical | Compound conditions reduce false positives but need real historical baselines to tune — not reliably tunable on a 5-day-old MVP dataset | Most prominent card-level indicator, reserved for rare cases | **Phase 2** (needs baseline history depth this hackathon won't have) |
| Cross-market correlation signal | Two related markets move together | Requires a defined "related markets" mapping | Not defined for MVP | — | High — correlation ≠ meaningful relationship, easy to overstate | N/A | **Excluded from MVP**, revisit only with the curated related-market set already planned for the demo issues |
| Context-candidate timing overlay | A change episode and a verified candidate occupy a compatible review window | Stored episode, verified candidate, citation sources | N/A — display only, not a computed trigger | — | Highest causal-misread risk of any element in the product | Always shown as a candidate with an explicit no-relationship boundary | **v3 manual; v4 automated only under ADR-038** |

### Severity tiers (naming)
- **Low signal** → not surfaced as a badge; just the default number.
- **Medium signal** → "Expectation Shift Detected" badge.
- **High signal** → "Issue Reassessment Signal" badge, shown with the movement explanation.
- **Critical signal** → "Unusual Market Activity" badge — reserve this tier for compound triggers only, and pair it with the strongest caution copy available, since this is exactly the tier most likely to be misread as "big news, act now."

### MVP recommendation
Ship only **Expectation Shift Detected** (the existing ±5pp inflection marker) for the hackathon. Everything requiring a volume/liquidity history baseline (Attention Spike, Unusual Market Activity, cross-market correlation) is Phase 2 — the 5-day timeline doesn't allow for properly tuning thresholds against real historical baselines, and a badly tuned "critical" signal is worse than not having one.

---

## 8. Participant Analysis Policy

This is the area with the highest ethical/legal exposure, because Polymarket's public trade/activity data is wallet-tagged and technically traceable, even though wallets are pseudonymous. The policy below is deliberately conservative.

### Allowed
| Feature | Product value | User risk | Ethical risk | Compliance concern | MVP feasibility | Decision |
|---|---|---|---|---|---|---|
| Aggregated participant count (unique wallets trading a market) | Rough breadth-of-engagement signal | Low | Low, if framed as "unique addresses" not "people" | Low | High | **Include** (nice-to-have, not blocking) |
| Overall activity increase (market-level) | Feeds the Attention score | Low | Low | Low | High (already covered by volume/trade-count data) | **Include** |
| Market-level participation trends over time | Context for "is this issue drawing more engagement" | Low | Low | Low | Medium (needs history) | **Include, Phase 2** |
| Distribution of public sentiment (e.g. share of volume on Yes vs No) | This is effectively just the price/outcome split — safe, already core to the product | Low | Low | Low | High | **Include** (this is just the existing probability metric) |
| Anonymous behavioral patterns (e.g. % of volume from small vs large trades, aggregated) | Adds texture to "is this move broad-based or concentrated" without naming anyone | Low–Medium | Medium — even aggregated "large trade share" can gesture at whale activity | Low | Medium | **Include with care** — present as a market-level concentration stat, never tied to any address |
| Category-level participation comparison | "Politics markets are seeing more activity than sports this week" style insight | Low | Low | Low | Medium | **Include, Phase 2** |

### Limited / Use Carefully
| Feature | Product value | User risk | Ethical risk | Compliance concern | MVP feasibility | Decision |
|---|---|---|---|---|---|---|
| Wallet-level activity (trade count/timing for a specific address) | Could support "concentration" metrics | Medium | High — one step from de-anonymizing a real trader's behavior pattern | Medium | Technically feasible via Data API, but should not be built as a browsable feature | **Limit**: use only internally to compute aggregate concentration stats; never expose a per-wallet view |
| Repeated participation patterns (same wallet active across many markets) | Could indicate a power user cohort at the aggregate level | Medium | High if it starts to look like profiling | Medium | Feasible | **Limit**: aggregate only ("X% of volume comes from repeat participants"), never list or link wallets |
| Historical behavior of public addresses | Same data is technically public on-chain, but publishing it in *this* product reframes it as "worth watching" | High | High | Medium–High | Feasible | **Limit** heavily; do not build a search/lookup feature for any address |
| Influence of large participants (whale share of volume) | Legitimate concentration/caution signal | Medium | Medium | Low–Medium | Feasible | **Limit**: fold into the confidence/caution badge ("a large share of recent volume came from a small number of addresses") — describe the market, not the wallet |
| Concentration of activity | Useful caution signal (thin, concentrated markets are less trustworthy) | Low–Medium | Low–Medium | Low | Feasible | **Limit**, same treatment as above — this is really a data-quality signal in disguise, so route it into Section 5's "confidence score," not a standalone participant feature |

### Not Allowed for MVP (or ever, without a strong separate justification)
| Feature | Why excluded |
|---|---|
| Ranking individual users by performance | Directly reframes the product as a trading leaderboard — contradicts the stated purpose and PRD's explicit non-goals |
| Identifying "expert traders" | Same as above, plus implies "follow this person's bets" |
| Showing real-time positions of specific users | Surfaces individual financial exposure — privacy and encouragement-to-copy risk, regardless of pseudonymity |
| Encouraging users to follow or copy participants | This is the single clearest line into "gambling/trading encouragement," which is the thing this product is explicitly designed not to be |
| Predicting what a specific participant will do next | Not just out of scope — actively incoherent with "we don't predict the future" positioning |
| Presenting participant behavior as betting guidance | Restates the core prohibition directly |

### Summary rule
If a participant-analysis feature can be described at the level of "this market" or "this category," it's likely fine. The moment a feature can be described at the level of "this wallet" or "this trader," it's out — full stop for MVP, and it requires a dedicated ethics/legal review before ever being considered post-MVP.

---
