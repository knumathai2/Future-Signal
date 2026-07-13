# Product Experience Design: Screen Flow, Copy Policy & Safety Guardrails for Outlook AI Signals

Document version: v1.0
Date: 2026-07-07
Companion to: [PRD](../prd/README.md) (hackathon PRD, v1.1), [Service Design](../service-design/README.md) (data/metrics/AI/signal design, v1.0)
Purpose: Define the screen flow, UI copy policy, gambling-pattern removal plan, disclaimer strategy, and prohibited-feature list for Outlook AI Signals, at a level ready to convert into wireframes and PRD requirement text.

**Scope note**: PRD scopes the 5-day hackathon MVP with no accounts, no save/watchlist, no notifications. This document designs the fuller product experience — including watchlist and settings — as the natural Phase 2 shape of the product, and marks clearly which screens are hackathon-buildable now vs. deferred. Where this document's recommendations differ from PRD's hackathon cut, the hackathon cut wins for the 5-day build; this document governs everything after.

---

## 1. Product Experience Design Summary

Outlook AI Signals reads like a **monitoring dashboard for how public expectations shift**, not a market terminal. The experience is built around three UX commitments that run through every screen below:

1. **Read-only, always.** No screen ever asks the user to act on a market. There is no "enter," no "place," no "follow this outcome." The only user actions are _view, filter, save-to-watch, and read a summary_.
2. **Every number has a companion caveat.** No probability, chart, or ranking appears without its interpretation-caution badge and a visible data-as-of timestamp in the same viewport.
3. **Vocabulary discipline is a UI contract, not a style guideline.** Section 4/5 below function as a lint list — any copy that fails it should block ship, the same way a failing test blocks a merge.

The screen flow is designed to move a user from **"what's changing" (Home) → "why does this matter" (Issue detail) → "how sure should I be" (caution/uncertainty) → "want to keep watching" (save)**, and never toward "what should I do about it."

---

## 2. MVP Screen Flow

```
Landing / Home
   |
   v
Issue List (ranked by expectation movement)
   |
   v
Market / Issue Detail  <----------------------+
   |                                          |
   +--> Probability Movement Analysis (chart) |
   |                                          |
   +--> Sudden Change Signal view             |
   |                                          |
   +--> AI-Generated Issue Report              |
   |                                          |
   +--> Related issues -------------------->--+
   |
   v
Save to Watchlist (Phase 2, requires lightweight account)
   |
   v
Watchlist screen (Phase 2)

Always reachable: Disclaimer / Information Policy screen, Settings
```

Entry is always into an **aggregate view** (Home or Issue List), never directly into a single market — this keeps the framing "issue landscape" rather than "market lookup," which matters for how the product reads on first impression.

### Screen inventory and hackathon status

| Screen                          | Hackathon MVP (PRD)                           | This document's Phase 2 design                                                                    |
| ------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Landing / Home                  | Yes (P0)                                      | Same, extended with attention/heat metrics as they come online                                    |
| Issue List                      | Yes (P0, as "急변 이슈 목록")                 | Same, extended with category filter and volume-based sort                                         |
| Market / Issue Detail           | Yes (P0)                                      | Same, extended with uncertainty score, attention badge                                            |
| Probability Movement Analysis   | Yes, folded into Detail (P0)                  | Split into a dedicated deep-dive view once volatility/momentum metrics exist                      |
| Sudden Change Signal view       | Partial (inflection marker only, P0)          | Full signal detail view once Attention Spike / Unusual Activity ship                              |
| AI-Generated Issue Report       | Yes, as template summary card (P0)            | Same shape, richer once more metrics feed the template                                            |
| Saved issue / Watchlist         | **No** (excluded from hackathon per PRD §6.5) | Phase 2, requires minimal account (see Section 12)                                                |
| Disclaimer / Information Policy | Yes (footer text, P0)                         | Promoted to a dedicated screen + persistent footer                                                |
| Settings                        | **No**                                        | Phase 2 — only once notifications or personalization exist; nothing to configure in hackathon MVP |

---

## 3. Screen-by-Screen UX Policy

### 3.1 Landing / Home

- **Purpose**: Show, at a glance, which public issues have seen the biggest shift in reflected expectation recently.
- **Main user action**: Scan the top-movers list; click into an issue.
- **Key information**: Today's top issues by movement, 24h/7d toggle, data-as-of timestamp, category filter.
- **Emphasize**: The _direction and magnitude of change_, framed as "expectation reflected in public data," and the caution badge on any thin/volatile entries.
- **Hide/minimize**: Anything resembling a "hot picks" tone — no badges that look like "trending stock," no fire/rocket icons implying opportunity.
- **Betting-perception risk**: **Medium** — a ranked list of "movers" structurally resembles a market-mover ticker. Mitigate with framing copy ("Today's most reassessed public issues") and non-financial iconography.
- **UX direction**: Editorial/dashboard tone (think "a data journalism front page"), not a ticker tape. Static card grid, not a scrolling live-price feed.
- **Shared header**: Desktop primary navigation sits in the same
  right-aligned group used by issue detail and list screens. When refresh is
  available it follows the navigation in that group; the navigation must not
  drift into a centered layout on the home route. Mobile retains the shared
  three-column navigation row.

### 3.2 Issue List

- **Purpose**: Let a user browse or filter the full monitored set, not just the top movers.
- **Main user action**: Filter by category, sort by recency of change, open an issue.
- **Key information**: Title, category, current expectation value, 24h/7d change, caution badge.
- **Emphasize**: Breadth of coverage and easy scanning; clear labeling of "expectation value," never "odds."
- **Hide/minimize**: Any sort option framed as "best opportunity" or "biggest swing to catch" — sort labels should read "Largest change (24h)," not "Biggest movers to watch."
- **Betting-perception risk**: **Medium** — a sortable list with percentages is visually close to an odds board. Mitigate with typography/layout that looks like a research index, not a trading screen (e.g., no monospace ticker font, no dense multi-column price-grid look).
- **UX direction**: Card or row list with generous whitespace, editorial typography, not a dense grid of numbers.
- **Visual emphasis**: Use a small terracotta heading marker, soft
  terracotta selected filters/result count/current reflected expectation
  values, and muted-blue comparison values. List-row hover may use the soft
  terracotta surface, but the entire resting list remains neutral. Direction
  continues to rely on the sign and label rather than green/red coding.

### 3.3 Market / Issue Detail

- **Purpose**: Give the full picture for one issue — what it's asking, how the reflected expectation has moved, and how much to trust that read.
- **Main user action**: Read the summary, view the chart, check the caution badge, optionally save (Phase 2).
- **Key information**: Title, plain-language description, current expectation value, 24h/7d/30d change, chart, caution badge, v3 curated candidate or v4 verified context candidate, data-as-of timestamp.
- **Emphasize**: The explanatory summary and the caution badge, positioned with equal visual weight to the number itself — never let the raw percentage be the loudest element on the page.
- **Hide/minimize**: Outcome-option labels should never be styled as selectable/clickable (no button-like affordance on "Yes"/"No" — see Section 6).
- **Betting-perception risk**: **High** — this is the screen closest to a market page. Mitigate by never showing "Yes/No" as tappable buttons, never showing both outcomes side-by-side with color-coded pricing (see Section 6.1).
- **UX direction**: Report-style layout — headline number, then narrative summary, then chart, then caveats. Chart and number should not be styled like a live trading widget (no ticking/animating price, no green/red flash on update).

### 3.4 Probability Movement Analysis (chart deep-dive)

- **Purpose**: Let a user explore the time series in more depth — zoom into a window, see inflection points.
- **Main user action**: Toggle time window, hover/tap for point-in-time values.
- **Key information**: Line chart of expectation value over time, inflection markers, window selector (24h/7d/30d).
- **Emphasize**: The shape of change over time; inflection points as "moments worth a closer look," not as trade entry/exit points.
- **Hide/minimize**: No candlestick-style rendering (that's an unmistakably trading-chart visual grammar) — line chart only. No axis labeled with currency or "price."
- **Betting-perception risk**: **High** if styled like a stock chart; **Low** if styled like a data-journalism line chart (e.g., FiveThirtyEight/NYT-style).
- **UX direction**: Single clean line, muted single-color palette (not green/red), soft-shaded uncertainty band around volatile stretches if feasible.

### 3.5 Sudden Change Signal screen

- **Purpose**: Explain, for an issue that triggered a signal, what changed and why the signal fired.
- **Main user action**: Read the explanation; understand it's a "look closer" flag, not an "act now" flag.
- **Key information**: Signal name (from Section 5's neutral vocabulary), magnitude/window, plain-language explanation, caution badge.
- **Emphasize**: That this is a _monitoring flag about data_, explicitly not a recommendation.
- **Hide/minimize**: No countdown timers, no "expires in," no urgency-styled color (red flashing, siren icons).
- **Betting-perception risk**: **Very High** — "signal" screens are the single most alert/trading-coded surface in the product. Mitigate hardest here: neutral naming (Section 7 of Service Design), muted color, no push-style urgency.
- **UX direction**: Treat like a "notable change" annotation on a news dashboard, not a trading alert card. No bell/alarm iconography.

### 3.6 AI-Generated Issue Report screen

- **Purpose**: Present the template-based summary (per Service Design §6) as a standalone, shareable/readable artifact.
- **Main user action**: Read; optionally copy/export text for content use (per PRD's content-creator persona).
- **Key information**: Issue summary, movement explanation, related-event candidate (if any), caution summary, disclaimer footer.
- **Emphasize**: That it's a _data summary_, not "AI's opinion" or "AI's prediction" — label it "Data Summary" or "Issue Report," not "AI Insight" or "AI Prediction."
- **Hide/minimize**: No confidence percentage on the AI's own output (that invites "how sure is the AI this will happen" misreadings, conflating model confidence with outcome likelihood).
- **Betting-perception risk**: **Medium** — AI-generated text can feel more authoritative/prescriptive than a raw number, so wording discipline matters even more here than elsewhere.
- **UX direction**: Plain report/document layout, generous line height, disclaimer footer always visible without scrolling past it.

### 3.7 Saved issue / Watchlist screen (Phase 2)

- **Purpose**: Let a returning user quickly check on issues they're monitoring.
- **Main user action**: Add/remove from watchlist, revisit saved issues.
- **Key information**: Saved issue cards (same shape as Issue List cards) with a "last checked" or "changed since you saved" indicator.
- **Emphasize**: "Changed since you last viewed," framed as an update to your monitoring list, not a portfolio.
- **Hide/minimize**: Absolutely no aggregate "gain/loss" framing across the watchlist (no portfolio-style total). This is the single highest-risk pattern to avoid — a watchlist with an aggregate delta reads exactly like a portfolio tracker.
- **Betting-perception risk**: **High** if it aggregates into a single number; **Low** if each item stays independent.
- **UX direction**: List of independent cards; never a summed/portfolio header. Consider explicitly avoiding the word "portfolio" anywhere in copy or code-facing naming, since naming leaks into UI text over time.
- **MVP status**: Deferred to Phase 2, requires minimal account system (see Section 12, Open Questions).

### 3.8 Disclaimer / Information Policy screen

- **Purpose**: Give users a single place to read the full policy statement (what this is, what it isn't, data limitations).
- **Main user action**: Read; this screen has no other action.
- **Key information**: Full policy text (Section 8 below), link from footer and onboarding.
- **Emphasize**: Plain language over legal language; short paragraphs.
- **Hide/minimize**: Nothing — this screen should be maximally visible, not buried.
- **Betting-perception risk**: N/A — this screen exists specifically to reduce that risk.
- **UX direction**: Simple static content page, linked persistently from the global footer.
- **Visual emphasis**: Use the shared terracotta heading marker and
  eyebrow, an outlined soft-accent return action, and numbered neutral cards
  with soft-accent number markers. Desktop may use two columns; mobile returns
  to one column. The explanatory body remains ink/neutral so emphasis does not
  make policy text feel promotional.

### 3.9 Settings screen (Phase 2)

- **Purpose**: Manage notification preferences (once notifications exist) and display preferences.
- **Main user action**: Toggle notification categories, adjust units/timezone.
- **Key information**: Notification frequency controls, data-refresh preference, link back to disclaimer.
- **Emphasize**: User control over notification frequency, positioned as reducing noise, not increasing engagement.
- **Hide/minimize**: No "turn on alerts to never miss an opportunity" style copy anywhere in this screen.
- **Betting-perception risk**: **Low**, as long as notification copy itself stays neutral (see Section 8, notification example).
- **UX direction**: Simple form/list UI; not needed at all for hackathon MVP since there's nothing to configure yet.

### 3.10 Change episode

- **Purpose**: Show one observed metric interval, any verified public context in
  the compatible review window, source provenance, what remains unknown, and
  interpretation caution as one evidence-first surface.
- **Order**: Observed change → verified context (when present) → sources →
  relationship boundary → what to check → data limitations → caution.
- **Required states**: zero, one, and three verified candidates; loading;
  not-yet-generated; and request failure. Zero candidates hide the entire
  context/source region without treating absence as an error.
- **Evidence connection**: Chart marker, episode, report metric reference, and
  candidate cards use the stored episode/candidate IDs. The UI does not infer a
  match by title or timestamp alone.
- **Source display**: Show source title, domain, optional published date, and a
  safe new-window link. Never show model text excerpts or internal scores.
- **Safety**: Data-as-of and a short caution stay in the same viewport as the
  change. The detailed relationship boundary states that timing does not
  establish a relationship with the observed movement.

### 3.11 Four-part issue detail navigation

- **Purpose**: Replace the long single-column detail reading path with four
  question-led tabs: `개요`, `AI 이슈 브리핑`, `관련 자료`, and `해석 안내`.
- **Overview**: Shows issue identity, the reflected expectation value, observed
  change, caution, data-as-of time, chart, and a compact set of items to check.
- **AI issue briefing**: Preserves the existing explicit generation action,
  loading/generating/fresh/stale/failure/last-good states, validated-block
  rendering, source cards, timestamps, and caution.
- **Related materials**: Separates dated candidate material from accepted v8
  sources. Dated items may be placed at the nearest chart observation only
  with a visible statement that timing does not establish a relationship.
- **Interpretation guide**: Explains the reflected expectation value, percent
  versus percentage points, activity/liquidity, inflection markers, refresh
  timing, and interpretation limits, with a link to the full methodology.
- **Shared context**: Every non-overview tab starts with issue identity, current
  reflected expectation value, seven-day observed change, caution badge, and
  data-as-of time. No tab may become a number-bearing surface without them.
- **Navigation**: The active tab is deep-linkable through the `tab` query
  parameter, preserves unrelated query parameters, supports Arrow/Home/End
  keyboard navigation, and uses a horizontally scrollable tab rail at narrow
  widths without causing page-level overflow.
- **Visual emphasis**: Use warm terracotta only for the active tab, current
  reflected expectation value, chart line/markers, timeline numbers, and the
  primary briefing action or summary edge. Use muted blue for comparison
  values regardless of direction; direction continues to rely on sign and
  wording rather than gain/loss color semantics.
- **Responsive acceptance**: No horizontal overflow at 320px, 375px, or desktop.

### 3.12 Scenario-conversation navigation

- **Purpose**: Add a distinct `시나리오 대화` tab for free-form conditional
  exploration without mixing assumptions into the stable briefing or accepted
  source flow.
- **Boundary**: The scenario tab is a fifth peer and remains separate from
  `AI 이슈 브리핑`; it does not change v8 briefing behavior.
- **Session**: One anonymous, issue-scoped session lasts at most 24 hours and
  eight user turns. It is not an account, saved history, or cross-device state.
- **Presentation**: Each assistant response carries a compact conditional label;
  current information and user assumptions remain distinguishable. Accepted
  source links render separately from authored prose.
- **Safety**: No raw HTML, model-authored active links/media, urgency styling,
  countdown, or direction-colored emphasis. Data-bearing responses retain the
  data-as-of time and caution.
- **Failure**: A failed current turn disappears while earlier validated turns
  remain. Expired/deleted sessions become unavailable without exposing
  authorization detail.
- **Transport**: Authenticated fetch-SSE renders complete validated blocks
  progressively in sequence; raw provider fragments never render.
- **Activation**: Application flags default to disabled. The checked-in
  production Compose profile enables the scenario API and generation workers
  explicitly.

---
