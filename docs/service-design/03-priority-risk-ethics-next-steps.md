# Service Design: Final Scope, Risk, and Ethics

_Source: implemented service boundaries and permanent safety constraints._

---

## 9. Final Feature Boundary

**Implemented**

- Binary issue discovery, ranking, categories, detail, and 24h/7d/30d history
- Aggregate volume and liquidity context, fixed change metrics, heat ranking, and
  caution states
- Evidence-bounded v8 briefings with validated source attribution
- Issue-scoped anonymous scenario conversations with strict premise and output
  validation
- Timestamped fallback data and explicit empty or zero-source states

**Excluded**

- Accounts, watchlists, notifications, newsletters, and team sharing
- Wallet-level browsing, participant rankings, following, or profiling
- Multi-outcome market support
- Unsupported or causal external-event matching
- Predictive recommendations, financial actions, and urgency-driven alerts

## 10. Risk and Mitigation

| Risk                                                                                               | Likelihood         | Impact | Mitigation                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------- | ------------------ | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Metrics get read as forecasts despite framing                                                      | High               | High   | Every number-bearing surface pairs with caution copy; no metric is ever shown without its companion badge (enforced as a UI-layer rule, not just a style guideline)                            |
| Thin-market noise triggers false "sudden change" signals                                           | High               | Medium | Ship only the single, already-scoped ±5pp marker for MVP; gate anything volume/liquidity-based behind Phase 2 baseline data                                                                    |
| AI drifts into causal or predictive language over time (prompt/template drift)                     | Medium             | High   | Keep AI outputs template-constrained with fixed slots; if an LLM is used for phrasing, constrain it with a fixed system prompt and validate output against a banned-phrase list before display |
| Wallet/participant data creeps from "aggregate" into "identifiable" as features are added post-MVP | Medium             | High   | Treat Section 8's "not allowed" list as a standing gate on every future feature proposal, not a one-time decision                                                                              |
| Comments/discussion data gets added later without re-checking API terms                            | Low (excluded now) | Medium | Re-run a ToS/legal check before ever adding this, don't assume MVP-era research still holds                                                                                                    |
| Users interpret "confidence score" as "confidence this will happen"                                | Medium             | High   | Never place the confidence/caution score adjacent to the probability number without a label; user-test the exact wording before shipping                                                       |

---

## 11. Data Ethics and Safety Guidelines

1. Collect only public market and aggregate activity data — no accounts, no personal data, no funds handling.
2. Never expose wallet-level detail as a browsable or searchable feature, even though the underlying data is technically public.
3. Every AI-generated or template-generated sentence about a market must be checked against a banned-phrase list (buy/sell/hold, guaranteed, will happen, follow, recommend, signal to act) before it ships — this should be a lint step, not a review-time judgment call.
4. Every metric or chart must be accompanied by a data-as-of timestamp and, where confidence is below threshold, a caution badge — no exceptions for "obviously fine" markets.
5. Related-event candidates are always labeled "candidate for context," never "cause," anywhere they appear (card, detail page, AI output).
6. Re-review this policy before adding any new data source (comments, wallet activity, external news feeds) — the ethics review is per-source, not one-time for the whole product.

---
