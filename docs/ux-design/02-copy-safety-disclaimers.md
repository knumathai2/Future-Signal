# UX Design: Copy Policy, Safety Guardrails, Disclaimers

_Source: former project-root UX Design sections 4-8._

---

## 4. Button and Copy Policy

Copy is treated as a compliance surface, not just a design surface. Every string that ships should be checkable against the three-tier list below before merge — in practice this can literally be a banned/careful-word lint step in CI, using the lists in Section 5.

### Policy by category

| Category | Rule |
|---|---|
| **Allowed** | Use freely. These describe observation, reading, and monitoring actions. |
| **Use Carefully** | Allowed only with a qualifying phrase attached in the same string or immediately adjacent (see examples below) — never standalone. |
| **Prohibited** | Never ship, in any context, including error states, placeholder/lorem text, internal debug labels that might leak to a user-facing build, or marketing copy. |

---

## 5. Safe Wording / Risky Wording / Prohibited Wording

### 5.1 Allowed wording

| UI context | Example |
|---|---|
| Primary CTA (issue card) | "View analysis" / "Read issue summary" |
| Chart section header | "Check probability movement" / "View trend" |
| Detail page CTA | "Explore public expectation" / "Open issue report" |
| Watchlist action (Phase 2) | "Monitor issue" / "Save issue" |
| Comparison feature | "Compare changes" / "See related issues" |
| Caution badge label | "View uncertainty" / "Data caution" |

**Reason these are safe**: every one of them describes a reading/observing action performed by the user on data, with no implied action on an outcome.

### 5.2 Use-carefully wording

| Word | Acceptable when... | Unsafe when... | Safe phrasing pattern |
|---|---|---|---|
| Signal | Paired with "monitoring" and a neutral noun: "Issue Reassessment Signal," "Expectation Shift Signal" | Standalone as "Signal!" or styled like a trading alert | "[Neutral noun] Signal Detected" always as a full compound phrase, never the bare word |
| Alert | Only inside Settings as a *notification category name* the user configures, never as urgency-styled UI copy | "Alert: act now," or paired with red/urgent styling | "Notify me about issue changes" — prefer "notify" over "alert" entirely if possible |
| Watch | As "watchlist" / "monitor" noun forms | As a verb implying market-watching for opportunity ("watch this one closely") | "Add to watchlist," "Monitoring list" |
| Momentum | Only as a labeled metric name with a defined, disclosed calculation ("Momentum score: consistency of recent directional change") | Used loosely to imply "this is going somewhere" | Always pair with "score" and a one-line definition on hover/info icon |
| Confidence | Only as "data confidence" / "confidence in the data reading," never adjacent to the probability number itself | As "73% confidence" next to a price (reads as outcome confidence) | Rename to "Data reliability" wherever possible to remove ambiguity entirely |
| Market activity | As a neutral descriptor of volume/trade count | Framed as "market activity suggests X will happen" | "Trading activity: [level]" as a standalone descriptive stat |
| Probability spike | Only as a labeled, defined event name tied to the signal system | Used as a headline/notification hook ("Probability Spike! Check now") | "A short-term shift in reflected expectation was detected" |

### 5.3 Prohibited wording

| Word/phrase | Reason for restriction |
|---|---|
| Bet, Buy, Sell, Trade | Directly reframes the product as a transactional/trading tool |
| Position, Long, Short | Trading-position vocabulary; implies the user holds or should hold a stake |
| Profit, Win rate | Implies financial outcome tracking, which this product must never do |
| Copy trader, Follow this user, Expert trader | Directly contradicts the participant-analysis policy (Service Design §8) — no following/copying framing anywhere |
| Best pick, Recommended outcome | Implies the product endorses an outcome — the single clearest line the product cannot cross |
| High-return opportunity | Financial-return framing, unambiguous violation |
| Guaranteed prediction | Contradicts the entire epistemic stance of the product (nothing here is a guarantee of anything) |

Any occurrence of these strings (including inside dynamically generated AI/template text) should hard-block release — treat this list as equivalent to a profanity filter, enforced automatically, not just documented as guidance.

---

## 6. Gambling-like Element Removal Plan

| Element | Why it may look like gambling | Safer alternative | Recommended copy | MVP decision |
|---|---|---|---|---|
| Probability display | A single "% chance" reads exactly like betting odds | Label it as "expectation reflected in market data," always paired with a caution badge, never shown alone | "Expectation value: 63% (as of [time])" | **Redesign** — keep the number, change the label and add mandatory badge |
| Market cards | Side-by-side Yes/No pricing with color coding mirrors a betting slip | Show only the tracked outcome's expectation value and its change, not a two-column odds table | Single value + change arrow, no second column | **Redesign** |
| Ranking pages | A "top movers" list resembles a leaderboard of hot bets | Frame explicitly as "issues under active reassessment," sort by data-based change metric only, never by "opportunity" | "Today's most reassessed issues" | **Redesign**, keep the ranking mechanism, change framing/labels |
| Graphs and charts | Candlestick/ticker-style charts are unmistakably trading visual grammar | Plain line chart, single muted color, no live-ticking animation | — | **Redesign** to line-chart-only, no exceptions |
| Sudden change signals | "Alert" framing plus red color plus urgency copy is a direct match to trading-alert UX | Neutral naming (Section 5.2), muted color, framed as "worth a closer look" not "act now" | "Expectation Shift Detected — worth a closer look" | **Redesign**, keep the underlying detection, change all surface treatment |
| Participant-related information | Any wallet-level or leaderboard framing turns this into "who's winning" | Aggregate-only stats per Service Design §8 (unique wallet count, concentration as a caution input) | "Trading activity: broad-based" / "concentrated among a few participants" | **Redesign to aggregate-only**; individual-level view is **excluded** entirely |
| Watchlist feature | Aggregate portfolio-style gain/loss view reads as a position tracker | Independent card list, no summed total, no "gain/loss since added" framing | "Changed since you saved this" (neutral, not gain/loss) | **Redesign**; build only in this constrained form, Phase 2 |
| Notification feature | Push notifications urging quick action mirror trading-app engagement patterns | Digest-style, user-configured frequency, neutral copy | "An issue you're monitoring has seen a notable change" | **Redesign**; not in hackathon MVP at all |
| AI report wording | Free-form, confident-sounding AI text can feel like a tip or a call | Template-constrained (Service Design §6), always paired with disclaimer | See Section 8 below | **Redesign** (already the plan) |
| Color usage | Green/red is the universal "gain/loss" signal in finance UIs | Use a single neutral accent color for "change," reserve green/red only if unavoidable for direction and desaturate heavily; consider blue/gray-scale + arrows instead of color alone | — | **Redesign**: prefer arrow/icon direction over color; if color is used, keep it desaturated and never paired with a $ or "+/-return" framing |
| Icons and visual metaphors | Fire emoji, rocket, coin, dice, slot-machine visual language reads as gamified/casino | Use chart/document/magnifying-glass/flag iconography — research and monitoring metaphors | — | **Redesign** — audit every icon against a "would this appear in a casino app" gut check |
| Empty states | "No bets yet — place your first bet!" style copy is an obvious anti-pattern to avoid, but even neutral products often default to overly game-like empty-state copy | Plain, functional copy | "No issues saved yet. Browse the issue list to start monitoring." | **Redesign**, low effort, do at launch |
| Onboarding messages | "Get ahead of the odds" style hooks read as a betting pitch | Frame around understanding, not advantage | "See how public expectations shift on major issues — for understanding, not prediction." | **Redesign**, this is pure copywriting, cheap to get right early |

---

## 7. Disclaimer Placement Strategy

Disclaimers repeat at every point a user could misread a number as a recommendation, rather than living in one buried policy page. Placement logic:

| Location | When shown | Why here |
|---|---|---|
| Onboarding (first screen, first session only) | Once, before any market data is shown | Sets the frame before the user sees a single number |
| Market/Issue Detail screen | Persistent, near the headline expectation value | This is the highest-risk screen (Section 3.3) — the disclaimer must sit next to the number it qualifies, not below the fold |
| AI Report screen | Persistent footer on every generated report | AI text feels more authoritative; needs its own reminder even if the user already saw it elsewhere |
| Sudden Change Signal screen | Inline, directly under the signal explanation | Highest urgency-misread risk (Section 3.5); must appear at the exact moment a user might feel "I should act" |
| Global footer | Persistent on every screen | Baseline, low-friction reminder; catches users who skip onboarding |
| Notifications (Phase 2) | Appended to every notification body, even if it lengthens the message | Notifications are seen out of context (lock screen, etc.) and need to stand alone |
| Terms/Policy screen | Full version, linked from footer and onboarding | Reference destination for the short-form reminders everywhere else |

Rule of thumb: **short-form disclaimer everywhere a number or signal appears; long-form disclaimer in exactly one dedicated screen.**

---

## 8. Disclaimer Copy Examples

**Onboarding screen**
> Outlook Signals shows how public expectations on major issues shift over time, based on public prediction-market data. This is an information tool — it does not predict outcomes, offer betting or investment advice, or recommend any action.

**Market / Issue Detail screen (short form, near the number)**
> This value reflects public trading activity, not a factual probability. Data may be incomplete or volatile — treat with caution.

**AI Report screen (footer, every report)**
> This summary is generated from public data and may contain errors or incomplete context. It is not advice of any kind. Please verify independently before relying on it.

**Sudden Change Signal screen**
> This flag highlights a notable shift in the data — it is not a recommendation to take any action. Sudden shifts can also reverse or reflect limited trading activity.

**Footer / global notice**
> Outlook Signals is an information analysis service based on public Polymarket data. It does not offer betting, gambling, investment, or financial advice.

**Notification message (Phase 2)**
> An issue you're monitoring shows a notable change in reflected expectation. This is for information only — not a recommendation to act. [View details]

**Terms-style policy summary (for the dedicated Disclaimer screen)**
> Outlook Signals is an information analysis and issue-monitoring service. It is not a betting, gambling, trading, or investment platform, and does not provide financial, legal, or political advice.
>
> Data shown is drawn from public Polymarket prediction-market activity. Prices reflect the expectations of market participants at a point in time — they are not certified facts, forecasts, or guarantees about real-world outcomes. This data can be incomplete, thinly traded, or highly volatile, and can change quickly or reverse.
>
> Any AI-generated or template-generated summaries are produced from this same data and may contain errors, omissions, or incomplete framing. They do not constitute advice.
>
> Do not make financial, legal, political, or other significant decisions based solely on information from this service. Always verify independently and consult a qualified professional where appropriate.

### 8.1 V5 AI summary and source-link presentation (ADR-048)

The detail screen visually separates `AI 이슈 브리핑` from deterministic
metrics and caution copy. The AI area shows a concise executive summary,
current-data interpretation, three to four conditional scenarios, factors to
check, observable materials/data updates, and verified-evidence synthesis when
available.

Verified source cards show source title, organization/domain, publication time,
source type, a neutral evidence summary, and a safe external action such as
`원문 확인`, `공식 자료 확인`, or `기사 원문 확인`. Link proximity must not imply
that the source explains the observed movement. The relationship boundary stays
visible beside the source region.

When no verified source exists, the source region remains visible with a plain
state explaining that no material passed the public criteria for the review
window and that the background of the numeric movement is not established. It
may link to the methodology page, but it must not link to an unverified result
or a generic external search.

Every AI summary retains report/data/episode timing and the interpretation
caution in the same report surface. Internal model names, scores, reasoning,
rejected URLs, and verification prompts remain non-public.

### 8.2 Approved v6 evidence-aware briefing presentation (ADR-050)

V6 renders only the sections allowed by the backend-selected report mode. A
significant change with verified material reads as observed change, verified
background, conditional interpretation, and exact source links. A significant
change without verified material replaces the background region with a compact
fixed absence state and general conditional scenarios. Stable modes begin with
an issue explanation and never style the stable value as an important movement.

General explanations and scenarios carry a visible and accessible notice with
this meaning: `현재 상황을 입증하는 검증 자료가 아니라 일반적인 시나리오
설명입니다.` Verified background uses a separate visual label. No-evidence
modes do not reserve an empty source-card region or provide unverified links.

The current value and change summary appear once in one observed-change region;
AI prose cannot repeat them. Exact resolution conditions, dates, exclusions,
and source reference move to `판정 기준 보기`, collapsed by default. The
control must support keyboard operation, `aria-expanded`, and visible focus.
Data-as-of timing and interpretation caution remain in the report viewport.

The strict frontend parser rejects unknown modes, extra or missing fields,
invalid evidence bases, source mismatches, and duplicated deterministic data.
Exact stored links alone open in a new tab with safe external-link attributes.
The user approved the v6 public API and AI-policy contract in
`reports/task-092-evidence-aware-briefing-policy.md` on 2026-07-11.

### 8.3 Approved v7 flexible briefing presentation (ADR-051)

V7 begins in an idle state with an explicit `AI 브리핑 생성` control. The
deterministic issue data remains readable during generation. Fresh, stale,
generating, and failed-with-last-good states show honest generated/data/context
times and retain the interpretation caution in the briefing surface.

The UI renders two-to-eight broad sections in the order returned by the strict
parser. Paragraph and short-list sections share consistent typography without
forcing the v6 four-mode layout. Market observations and external context stay
visually distinct even when their section order varies.

Source cards show exact stored title, domain, time, supported-claim summary,
and visible A/B/C level. Level C material is always attributed. Exact stored
safe URLs alone are interactive. The presence of a source must not imply that
it explains the observed movement.

### 8.4 Approved v8 issue-centered briefing presentation

V8 keeps the same request, cache, timestamp, caution, and source-card states but
changes the authored reading order. The headline and summary begin with the
issue and its currently confirmed situation. Sections then move through recent
change, interpretation boundaries, key conditions, and later information to
check. Section titles remain natural Korean rather than exposing internal data
categories. If the writer supplies a `limitations` section, the UI does not
repeat the deterministic data-limitations card; interpretation caution remains
visible in every full report state.

### 8.5 V8 source-refresh action

TASK-113 makes the existing briefing action request a bounded public-source
refresh before writing. The adjacent copy states that available public material
will be checked and then used with the current evidence bundle. Generating,
failure, last-known-good, source-card, timestamp, and caution states remain
unchanged; an empty accepted-source set is still shown explicitly rather than
filled with unverified material.

---
