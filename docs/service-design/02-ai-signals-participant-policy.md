# Service Design: AI I/O, Sudden Signals, Participant Policy

_Source: former project-root Service Design sections 6-8._

---

## 6. AI Input / Output Design

**Design decision consistent with PRD §8.8: the default AI is a template-filling engine over computed metrics, not a free-form LLM analyst.** An LLM may be used only to smooth the phrasing of a template-constrained output — never to generate open-ended interpretation, causal claims, or predictions. This is both a safety constraint and a scope constraint: free-form LLM analysis was explicitly deferred in the hackathon PRD (§6.5) pending a proper evaluation/guardrail framework.

### AI Inputs (all structured, all pre-computed — no raw scraping handed to a model)
- Market title, description, category
- Outcome definition (for binary MVP: which side "the price" refers to)
- Probability history for the selected window
- Volume history for the selected window
- Computed metrics: change %, volatility, attention, heat, confidence/caution level
- v3 manually curated related-event candidates; v4 verified context candidates
  may be included only from stored `url_citation` evidence accepted under
  ADR-038
- User-selected time range
- Data-as-of timestamp

### AI Outputs

| Output | Purpose | Required input | Format | Example | Limitations | Safety constraints |
|---|---|---|---|---|---|---|
| Issue summary | One-paragraph plain-language framing of what the market question is about | Title, description, category | 2–3 sentences | "This market tracks whether [event] will be resolved as 'Yes' by [date], based on public trading activity on Polymarket." | Can't add outside context the description doesn't contain | Must not restate the question as if it were a real-world fact |
| Probability movement explanation | Describes the size/direction/timing of a change | Price history, change %, inflection points | Template with computed values filled in (matches PRD §8.8 template exactly) | "Over the past 7 days, the expectation reflected in this market rose by 8.2 percentage points, with the largest shift occurring around [date]." | Says *what* moved, never *why* with certainty | No causal verbs ("because," "due to," "caused by") — use "coincides with," "occurred alongside" |
| Key change factors | Surfaces the manually curated related-event candidate, if one exists for this market | Related-event candidate list | 1 sentence, clearly labeled as a candidate | "A related event candidate around this time: [event]. This is offered as context, not as a confirmed cause." | Only available for the curated demo set in MVP | Must always carry the "candidate, not cause" qualifier — no exceptions |
| Neutral context comparison | Compare verified public information with a change episode without asserting a relationship | Verified candidate sources, price history, evidence IDs | Short structured section | — | Approved for TASK-056~065 v4 | Same causal-language ban applies; missing evidence fails closed |
| Market trend summary | Rolls up change/volatility/attention into one readable status line | All computed metrics | 1 sentence | "This issue has seen a moderate, steady increase in reflected expectation over the past week, with typical trading activity." | Purely descriptive of computed values | Must not use words like "trending toward" a specific outcome |
| Sudden change explanation | Explains a triggered signal (Section 7) in plain language | Signal type, magnitude, window | 1–2 sentences | "A larger-than-usual shift in reflected expectation was detected in the last 6 hours, alongside increased trading activity." | Only as good as the threshold tuning | Must use the neutral signal vocabulary from Section 7, never "alert" framing |
| Risk / uncertainty summary | States the interpretation-caution basis in plain language | Confidence/uncertainty score inputs | 1 sentence | "Trading activity on this market has been limited recently, so this change should be interpreted with caution." | Can't quantify precisely how much caution is "enough" — stays qualitative | Always appears attached to the metric it qualifies, never standalone |
| Related issue clustering | Groups markets by category/topic for browsing | Category, tags | List | — | Category-based only in MVP; no semantic clustering | Cluster by topic, not by "similar outcome" (avoids implying correlated bets) |
| Timeline-based analysis | Chronological list of the market's own inflection points | Price history, detected inflection points | Timeline/list UI | — | MVP: single-market timeline only, no cross-market timeline | Each entry stays in "observed change" language |
| User-friendly report | Bundles summary + movement + caution into one shareable block | All of the above | Structured card (title, 3–5 sentence body, caution footer) | Matches PRD §8.8 template | This *is* the P0 "template summary" feature | Must always include the standard disclaimer footer (PRD §17.1) |
| Newsletter-style briefing | Batches several issue summaries for a periodic digest | Multiple issue summaries | Multi-section digest | — | **Phase 3** (PRD already defers "weekly report" to Phase 3) | Same per-item constraints as above, plus an overall disclaimer at the top of the digest |

### Hard constraints on every AI output (non-negotiable, enforce at the template/prompt layer, not just via instructions)
- No buy/sell/hold, position, or trade language.
- No "this will / won't happen" framing — only "expectation reflected in the data has moved."
- No "follow this trader/user" language (there is no per-user output surface at all — see Section 8).
- No numeric confidence stated as a probability of a real-world outcome (e.g., never "73% likely to happen" — only "the market-reflected value is 73%").
- No financial or betting advice, explicit or implied.
- Every output that touches a specific market must carry a caution qualifier if the underlying confidence/uncertainty score is below the "sufficient data" threshold.

### 6.1 Approved v4 research and verification contract

TASK-056~065 adds a bounded research step between signal detection and report
generation. It uses one research model with OpenRouter web search, parses only
API `url_citation` annotations, applies deterministic URL/domain/date/entity/
source-independence gates, and then uses a different model without web access
for independent verification. A model cannot override a failed hard gate.

Public candidates require either one official source directly supporting the
tracked condition or at least two independent sources supporting the same
event and date. Conflicts, weak entity/condition matches, generated URLs,
unsupported claims, verifier disagreement, and unsafe relationship language
produce `withheld` or `rejected` state and remain outside the public API.

Research, verification, and v4 writing share a cumulative USD 100 budget for
TASK-056~065. Per-run usage is audited without storing secrets, prompts, or full
responses. `no_candidate` is a successful result, and prior successful public
content remains available when the provider fails.

### 6.9 Approved v5 narrative-summary contract (ADR-048)

TASK-075~081 supersedes v4's two model-authored fields with six fixed narrative
fields: `executive_summary`, `current_data_interpretation`,
`conditional_scenarios`, `factors_to_check`, `signals_to_watch`, and nullable
`evidence_synthesis`. The model may write
natural Korean prose inside those fields, but it may use only the supplied
market definition, stored metric/snapshot values, and same-episode verified
context candidates. This is structured narrative generation, not evidence-free
or open-ended analysis.

Every number, date, named entity, event, and source statement must be traceable
to an input evidence reference. Generic prose that could be reused across
unrelated issues, unsupported claims, causal language, outcome assertions,
duplicated sections, incomplete Korean sentences, and prohibited wording block
storage. Deterministic relationship-boundary, data-limitation, and caution
fields remain mandatory and are reconstructed at read time.

Verified source cards expose the exact stored title, domain, publication time,
source type, and URL. No verified candidate means `evidence_synthesis=null` and
an explicit UI state that no source passed the public criteria; the system must
not substitute an unverified article or generic search link.

TASK-077 further requires three or four explicitly conditional scenarios,
typed issue-specific check/watch items, title/entity/condition/date/official-
domain search anchors, and deterministic rejection of market-listing or
forecast pages. These improvements do not weaken the same-window, official-
source, independent-source, annotation, or verifier gates.

### 6.10 Approved v6 evidence-aware briefing contract (ADR-050)

V6 selects one of four report modes with deterministic code before writer
invocation. The two inputs are independent: the latest linked metric qualifies
as a significant change only under the existing 24-hour ±5pp
`expectation_shift` rule, and verified material is present only when at least
one same-episode candidate survives the existing strict public read gates.

The four modes are `change_with_evidence`, `change_without_evidence`,
`stable_with_evidence`, and `stable_without_evidence`. Stable modes may not
inflate a below-threshold or unavailable movement. No-evidence modes may provide
clearly labelled general conditional scenarios, but those scenarios are not
evidence of the current situation and cannot add unsupported recent facts,
named-person states, concrete procedures, causal claims, likelihood rankings,
outcome assertions, or action prompts.

V6 separates `observed_data`, `market_definition`, `verified_context`,
`general_scenario`, and `data_limitation` bases. Current value, change amount,
metric time, mode, no-source state, limitations, caution, and resolution-rule
reference are deterministic. The writer receives only the authored fields
allowed by the selected mode. Exact resolution rules appear only in the
collapsed reference region, not in the briefing body. Generation and read paths
reject metric/rule repetition, cross-section duplicates, unsupported evidence
bases, and mode/field mismatches.

The exact decision table, response proposal, duplication checks, and approval
boundary are recorded in
`reports/task-092-evidence-aware-briefing-policy.md`. The user approved the
bounded AI-policy and public report API changes on 2026-07-11. This approval
does not authorize deployment, production writes, workflow mutation, new
dependencies, or a schema change.

### 6.11 Approved v7 on-demand briefing and source-level contract (ADR-051)

V7 separates market collection, context collection, and briefing generation.
Normal market collection never invokes the writer. An explicit user request or
approved development evaluation builds a fingerprinted evidence bundle and
creates or joins one generation request.

The writer receives opaque market-definition, metric, history, context,
source, and limitation references and returns a positive-first flexible
`headline`, `summary`, and two-to-eight broad sections. Section count, order,
title, and paragraph/list presentation may vary. The backend owns identifiers,
values, timestamps, source metadata, source level, cache state, caution, and
last-known-good selection.

Accepted sources use visible levels A (official/primary), B (established
reporting or recognized institution), or C (attributed supporting material).
Level D remains internal rejection. Every A-C source must pass deterministic
access, identity, relevance, time, supported-claim, duplicate, and
contradiction checks. A no-search verifier is reserved for conflict,
ambiguity, high-impact claims, strong relationship language, or materially
used level-C claims. It can withhold but cannot promote failed evidence.

Unknown or mismatched references, unsupported facts, unsafe links, invented
metadata, unattributed C material, unsupported future/causal assertions, and
irreconstructible envelopes block publication. Style, section ordering,
English terms, and moderate repetition are quality diagnostics. The exact
contract is `reports/task-101-v7-briefing-contract.md`.

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
