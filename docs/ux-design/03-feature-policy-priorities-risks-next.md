# UX Design: Feature Policy, Priorities, Risks, Open Questions, Next Steps

_Source: former project-root UX Design sections 9-15._

---

## 9. Prohibited Feature List (Strictly Prohibited — never in MVP or later without a full product-position change)

| Feature | Why risky | Behavior it may encourage | Safer alternative | Decision |
|---|---|---|---|---|
| Bet placement / links directly guiding users to place bets | Turns the product into a betting funnel outright | Directs users to actually gamble | None — remove entirely; if linking to Polymarket at all is ever considered, it must not be styled or worded as a call to place a bet | **Exclude, permanently** |
| Buy/sell/position recommendations | Direct financial-advice framing | Trading on the app's say-so | Descriptive movement explanation only (Service Design §6) | **Exclude, permanently** |
| Outcome recommendations ("this will likely happen") | Contradicts the entire epistemic premise of the product | Overconfidence in an uncertain outcome | "Expectation reflected in data has moved to X" | **Exclude, permanently** |
| Real-time trader following / copy-trading | Directly contradicts Service Design §8's participant policy | Copying an anonymous trader's position | Aggregate-only participant stats | **Exclude, permanently** |
| User ranking by profit/win rate | Leaderboard-of-gamblers framing | Chasing "top performer" status | None needed for this product | **Exclude, permanently** |
| Wallet-based "expert" discovery | Same as above, plus identifiability risk | Seeking out and following a specific address | None | **Exclude, permanently** |
| Notifications urging quick action ("act now," "don't miss") | Classic trading-app engagement dark pattern | Impulsive checking/acting behavior | Neutral, digest-style notification copy (Section 8) | **Exclude, permanently** |
| Personalized betting suggestions | Direct advice framing, personalized == higher perceived authority | Following an individualized "tip" | None | **Exclude, permanently** |
| "Best market to enter" recommendations | Same as outcome recommendations, worse because it implies timing advice | Acting on a perceived opportunity window | None | **Exclude, permanently** |
| Profit simulation / expected return calculator | Directly computes and displays financial outcomes — this is the clearest possible "this is a trading tool" signal | Rehearsing a bet before placing it elsewhere | None; if users want this, they should use Polymarket itself, not this product | **Exclude, permanently** |

---

## 10. Restricted Feature List

### 10.1 Excluded from MVP (not permanently banned, just not now)

| Feature | Reason for MVP exclusion | Revisit condition |
|---|---|---|
| Individual wallet performance analysis | Ethical/identifiability risk per Service Design §8 | Only reconsider paired with a legal review; likely never becomes "individual," at most "aggregate concentration" |
| Participant leaderboard | Same as above, plus directly gambling-coded | Not planned to revisit |
| Real-time position tracking | Implies live financial exposure tracking | Not planned to revisit |
| Automated prediction recommendation | Contradicts product premise | Not planned to revisit |
| Aggressive push alerts | Dark-pattern engagement risk | Revisit only as neutral, user-controlled digest notifications (Phase 2, Section 3.9) |
| Social following of participants | Participant policy violation | Not planned to revisit |
| High-risk market ranking (e.g., "most volatile — biggest swings") | "High risk" framing reads as a risk/reward pitch even if intended as a caution flag | Could revisit as "highest uncertainty" framing, folded into the caution badge system rather than a standalone ranked list |
| User-specific "opportunity" feed | Personalized-opportunity framing is advice-adjacent regardless of neutral intent | Could revisit as a neutral personalized *monitoring* feed (issues in categories the user watches), if reframed away from "opportunity" language entirely |

### 10.2 Allowed only after legal / compliance review

| Feature | Why it needs review | What review should assess | MVP feasibility absent review |
|---|---|---|---|
| Wallet-level historical behavior analysis | Pseudonymous but potentially identifiable; unclear regulatory posture on republishing on-chain trade history | Data-privacy exposure, applicable financial-services regulation, ToS of the data source | **Not feasible now** |
| Large participant concentration analysis | Adjacent to the above, lower risk if kept aggregate-only (already partially allowed per Service Design §8) | Whether "concentration %" can be computed without any addressable/traceable detail | **Partially feasible now** as an aggregate caution input only (already scoped) |
| Market anomaly detection (beyond the basic signal system) | Could imply market manipulation detection, a claim this product isn't positioned or resourced to make responsibly | Legal exposure of implying manipulation/integrity claims about a third-party market | **Not feasible now** |
| Advanced alerting (e.g., predictive/pre-emptive alerts) | Risk of drifting from "notable change occurred" to "change is about to occur" | Whether the underlying model can support "predictive" framing without becoming a forecasting claim | **Not feasible now** |
| User-personalized issue recommendations | Personalization can look like tailored advice even when the underlying content is neutral | Whether personalization logic can be scoped to categories/topics only, not "issues you should bet on" | **Feasible as category-based personalization only**, with careful copy review |
| Cross-market influence analysis | Correlation-implies-causation risk is high (flagged already in Service Design §7) | Whether correlation framing can be kept strictly descriptive and non-predictive | **Not feasible now** |

---

## 11. Safe Alternative Features

These are the "yes, but redesigned" replacements referenced throughout Sections 6, 9, and 10 — collected here as a build-ready list:

- Aggregate-only participation stats (unique wallet count, activity concentration folded into the caution badge)
- Category-level monitoring feed (personalization without "opportunity" framing)
- Independent-card watchlist with no aggregate total
- Digest-style, user-controlled notifications with neutral copy
- Uncertainty/caution badge system as the replacement for any "risk ranking" impulse
- Template-constrained AI reports instead of free-form analysis
- Line-chart-only visualization instead of any trading-chart grammar
- Neutral signal vocabulary (Section 5.2) instead of alert/urgency language

---

## 12. MVP UX Priorities

Reconciling with PRD's hackathon scope and Service Design's data/metric priorities:

**Ship in hackathon MVP**
- Home, Issue List, Issue Detail, Probability Movement (folded into Detail), basic Sudden Change marker, AI Report (template), Disclaimer footer + dedicated screen
- Full copy-policy enforcement (Sections 4–6) — this is nearly free to do right from day one and expensive to retrofit later
- Line-chart-only visualization, neutral color/iconography from the start

**Phase 2**
- Watchlist (requires minimal account — open question, see Section 14)
- Settings screen
- Notifications (digest-style only)
- Category-level personalization
- Dedicated Sudden Change Signal screen (richer than the hackathon's single inflection marker)

**Not planned / gated on review**
- Everything in Sections 9 and 10.2

### Approved post-MVP v4 exception

ADR-038 authorizes TASK-063's change-episode UI only after the schema, research,
verification, batch, report, and API predecessors pass. Public context must be
stored as `verified`, include stored citation-source metadata, and retain the
candidate-not-cause boundary. Withheld/rejected candidates, model-body URLs,
internal scores, and source excerpts never reach the UI. The v3 manual path
remains the historical MVP behavior until the strict v4 endpoint is available.

---

## 13. Product Risk and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Copy drifts toward trading language over time as new contributors add features | High | High | Automated banned-word lint (Section 5.3) in CI, not just a style guide humans are expected to remember |
| Watchlist becomes a de facto portfolio tracker once an aggregate view feels "obviously useful" to a future contributor | Medium | High | Explicit design rule in Section 3.7: no summed/aggregate delta, ever; flag this rule in the component's code comments, not just this doc |
| AI-generated text drifts into confident/predictive tone as templates are extended | Medium | High | Every new AI output type must pass through the same banned-phrase check as existing ones before ship (Service Design §6) |
| Notification feature (Phase 2) gets redesigned later toward urgency to boost engagement metrics | Medium | High | Treat "no urgency-styled notifications" as a standing product principle to re-assert whenever a growth-oriented redesign is proposed |
| Visual design (color, icons) inherited from a generic fintech/trading UI kit reintroduces gambling-coded patterns by default | Medium | Medium | Explicit icon/color audit against the casino-app gut-check (Section 6) before any visual design system is finalized |
| Legal/regulatory posture on prediction-market data changes | Low–Medium | High | Revisit Section 10.2's gated features on any regulatory update; keep the product's "information only" framing conservative rather than pushing toward the line |

---

## 14. Open Questions

1. Does the Phase 2 watchlist require a full account system, or can it work with a lightweight, anonymous local-storage save (no login) to avoid building auth at all? This affects whether Settings is needed at all in Phase 2 or can wait further.
2. Should the caution/uncertainty badge be a single composite indicator or multiple separate badges (data sufficiency, volatility, liquidity) — same open question as Service Design §12, but now also a UX question of how many badges a card can show before it gets visually noisy.
3. For notifications (Phase 2), what's the minimum viable frequency control that avoids both "too noisy" and "so infrequent it's useless" — needs user testing, not just a design guess.
4. Should the dedicated Disclaimer screen be a single static page, or does it need versioning (e.g., "last updated" date) if the policy text changes over time?
5. How should the product handle a market that resolves while a user has it saved on their watchlist — does it disappear, get archived, or get shown with a "resolved" state? This wasn't addressed in PRD and needs a decision before Phase 2 watchlist work starts.

---

## 15. Next Steps for PRD and Wireframe Creation

1. Turn Section 3's screen-by-screen policy into literal PRD requirement entries (purpose, main action, key info, acceptance criteria) in the same format as PRD §8 — this document's tables map almost directly.
2. Hand Section 5's three-tier word lists to whoever builds the copy/lint tooling — this should become an actual checked list in the codebase (e.g., a JSON banned/careful-word file referenced by both UI copy and AI template generation), not just documentation.
3. Use Section 6's element-by-element redesign table as the direct input for wireframing — each row's "safer alternative" and "recommended copy" can go straight into a wireframe annotation.
4. Resolve Section 14's open questions (especially #1, the watchlist auth question) before scoping Phase 2 engineering, since the answer changes whether Phase 2 needs an auth system at all.
5. Once wireframes exist, run them back through Section 6's "would this appear in a casino app" gut-check as a design review step, not just at the copy level — visual layout (card density, color blocking, animation) carries as much gambling-coded risk as wording does.
