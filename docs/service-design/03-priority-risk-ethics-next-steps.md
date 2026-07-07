# Service Design: Priority, Risk, Ethics, Open Questions, Next Steps

_Source: former project-root Service Design sections 9-13._

---

## 9. MVP Feature Priority

This reconciles with PRD §6.3–6.5. Additions from this document layered in:

**P0 (hackathon-buildable, matches PRD exactly)**
- Data: title, description, category, outcomes (binary), price, price history, volume, liquidity snapshot, dates, status
- Metrics: probability change (24h/7d), simplified issue-heat ranking, simplified confidence/caution badge
- AI: template-based issue summary + movement explanation + caution summary (no free-form LLM)
- Signal: Expectation Shift Detected (±5pp threshold marker)
- Participant data: none beyond what's already implicit in volume (no dedicated participant feature needed for MVP)

**P1 (build if time allows, needs slightly more data pipeline)**
- Volatility score, attention score, momentum score
- Aggregated unique-wallet count per market
- Manually curated related-event candidates for 3–5 demo issues (already in PRD)

**P2 / Phase 2+ (needs historical pipelines, tuning time, or policy sign-off this hackathon can't produce responsibly)**
- Volume-spike score, liquidity-change score, narrative-shift score
- Attention Spike / Unusual Market Activity signals (need real historical baselines)
- Category-level and time-series participation trends
- Aggregate concentration/whale-share stat folded into confidence badge
- Multi-outcome market support
- Newsletter-style briefing
- Any cross-market correlation feature

**Excluded outright for now**
- Comments/discussion data
- Any wallet-level browsable view
- Any participant ranking/following feature
- Automated news matching

---

## 10. Risk and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Metrics get read as forecasts despite framing | High | High | Every number-bearing surface pairs with caution copy; no metric is ever shown without its companion badge (enforced as a UI-layer rule, not just a style guideline) |
| Thin-market noise triggers false "sudden change" signals | High | Medium | Ship only the single, already-scoped ±5pp marker for MVP; gate anything volume/liquidity-based behind Phase 2 baseline data |
| AI drifts into causal or predictive language over time (prompt/template drift) | Medium | High | Keep AI outputs template-constrained with fixed slots; if an LLM is used for phrasing, constrain it with a fixed system prompt and validate output against a banned-phrase list before display |
| Wallet/participant data creeps from "aggregate" into "identifiable" as features are added post-MVP | Medium | High | Treat Section 8's "not allowed" list as a standing gate on every future feature proposal, not a one-time decision |
| Comments/discussion data gets added later without re-checking API terms | Low (excluded now) | Medium | Re-run a ToS/legal check before ever adding this, don't assume MVP-era research still holds |
| Users interpret "confidence score" as "confidence this will happen" | Medium | High | Never place the confidence/caution score adjacent to the probability number without a label; user-test the exact wording before shipping |

---

## 11. Data Ethics and Safety Guidelines

1. Collect only public market and aggregate activity data — no accounts, no personal data, no funds handling.
2. Never expose wallet-level detail as a browsable or searchable feature, even though the underlying data is technically public.
3. Every AI-generated or template-generated sentence about a market must be checked against a banned-phrase list (buy/sell/hold, guaranteed, will happen, follow, recommend, signal to act) before it ships — this should be a lint step, not a review-time judgment call.
4. Every metric or chart must be accompanied by a data-as-of timestamp and, where confidence is below threshold, a caution badge — no exceptions for "obviously fine" markets.
5. Related-event candidates are always labeled "candidate for context," never "cause," anywhere they appear (card, detail page, AI output).
6. Re-review this policy before adding any new data source (comments, wallet activity, external news feeds) — the ethics review is per-source, not one-time for the whole product.

---

## 12. Open Questions

1. Which category taxonomy to use for the 30–50 MVP markets — Polymarket's own tags, or a manual mapping? (Also open in PRD §20.4)
2. What minimum volume/liquidity floor should exclude a market from the ranking entirely vs. just badge it as low-confidence?
3. Is "unique wallet count" worth the aggregation-pipeline cost for MVP, or does it wait for Phase 2 alongside volume-history-dependent metrics?
4. Should the confidence/caution score be a single composite number or kept as separate qualitative badges (data-sufficiency, liquidity, volatility) — a single composite may be easier to over-trust.
5. For Phase 2 "concentration of activity" — what threshold of wallet-level detail is legally/ethically comfortable to fold into an aggregate stat, and does that require outside review before building?
6. Does a Phase 2 newsletter/briefing feature need a different disclaimer treatment than the single-issue view, given it batches multiple issues at once?

---

## 13. Next Steps for PRD Creation

1. Fold the P0 metric/signal definitions from Sections 5 and 7 into PRD §8.5–§8.7 as the authoritative calculation spec (this document's tables can become the engineering reference; PRD keeps the product-level requirement language).
2. Write the AI output templates from Section 6 as literal string templates (not prose descriptions) for the data/AI engineer to implement directly — one template per output type, with the banned-phrase list as an automated check.
3. Turn Section 8's "Allowed / Limited / Not Allowed" table into a standing checklist that any future feature proposal involving participant data must pass before being scoped.
4. Confirm the Section 2 data-field mapping against the actual Gamma/CLOB API responses during Day 1 data validation (PRD §14, Day 1) — this document assumes standard field availability but hasn't been checked against a live pull.
5. Once the hackathon MVP ships, use Sections 5–7's P1/P2 tables directly as the Phase 2 backlog — they're already prioritized and reasoned, so Phase 2 planning should start from pruning this list against real usage data, not from a blank page.
