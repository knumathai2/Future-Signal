# PRD: MVP Scope, Scenarios, Functional Requirements

_Source: former project-root PRD sections 6-8._

---

## 6. MVP Scope

### 6.1 Recommended MVP definition

A dashboard that selects global issues with large recent changes in reflected expectation value from public prediction-market data, and helps users quickly understand the flow of reassessment through change magnitude, time-series charts, and interpretation-caution text.

### 6.2 Implementation scope constraints

| Item | Hackathon MVP standard |
|---|---|
| Data scope | ~30-50 active markets |
| Market type | Binary markets, primarily |
| Change window | Primarily 24h, 7d |
| Chart window | 24h, 7d, 30d if possible |
| Refresh method | Pre-collected data + manual refresh, or limited scheduling |
| Inflection points | Simple threshold-based markers |
| Event candidates | v3: 3-5 representative issues, entered manually; v4: verified candidates only under ADR-038 |
| Summary | Numeric, template-based |
| User accounts | None |
| Sharing / saving | None |

### 6.3 P0: Must build

| Feature | Implementation approach | Reason |
|---|---|---|
| Home dashboard | Top-movers issue cards | First impression of the service |
| Sudden-change issue list | Sorted by 24h/7d change | Core value |
| Issue card | Title, category, current value, change, badge | Core information delivery |
| Issue detail screen | Chart + change summary + badge | Problem-solving flow |
| Time-series chart | Line chart based on price history | Data-service credibility |
| Change calculation | Current value - past value | Feasible and intuitive |
| Simple inflection-point display | Show segments with >=5pp change | Demo impact |
| Interpretation-caution badge | Based on activity level / data insufficiency / volatility | Legal and ethical safeguard |
| Template summary | Numeric, sentence-generated | Improves usability, reduces AI risk |
| Data as-of timestamp | Shown on every major screen | Builds trust |
| Disclaimer / caution text | Fixed display on dashboard and detail screens | Prevents product misunderstanding |
| 3 representative demo issues | Selected to fit the presentation flow | Persuasiveness for judges |

### 6.4 P1: Build if possible

| Feature | Build condition |
|---|---|
| Category filter | If source tags or manual mapping are stable |
| Activity-based sorting | If volume data is available |
| Inflection-point click tooltip | If frontend has spare capacity |
| Manual event candidates | Limited to representative issues |
| Empty/error state polish | If there's spare time after Day 4 |
| Responsive UI polish | For presentation quality |

### 6.5 P2: Excluded, or a direction for post-presentation expansion

| Feature | Handling |
|---|---|
| Chart image export | Explain as a Phase 2 feature for content creators |
| Saved/watchlist issues | Phase 2, after login |
| Change notifications | Phase 3 |
| Weekly report generation | Phase 3, after data accumulates |
| Team sharing | B2B expansion direction |
| Automated news matching | Deferred due to causal-misinterpretation risk |
| Free-form AI analysis | Introduced after safeguards and an evaluation framework exist |
| Per-user personalization | Beyond hackathon scope |
| Full multi-outcome market support | Deferred due to data-structure complexity |

---

## 7. Core User Scenarios

### 7.1 Representative scenario

A user opens the service to prepare a daily issue briefing. On the first screen, they check the list of issues with large 24-hour changes, click into a specific issue, and go to the detail screen. On the detail screen, they view the time-series chart of the reflected expectation value and simple inflection-point markers, then read the template summary card and interpretation-caution badge to understand how the issue is being reassessed.

### 7.2 Content-creator scenario

1. The user opens the dashboard in the morning.
2. They check the "today's most-changed issues" list.
3. They select an issue with a large change.
4. On the detail screen, they check the chart, inflection points, and data summary.
5. They use "which direction the reflected expectation value moved, according to public data" in their content draft.
6. They also check the interpretation-caution text to avoid overstated language.

### 7.3 Researcher / planner scenario

1. The user opens the dashboard before a meeting.
2. They compare issues by 24h/7d change.
3. They check a specific issue's detail chart.
4. They check the value change before and after the inflection point.
5. They check the activity-level or volatility caution badge.
6. They incorporate "observed change" and "points needing further verification" into their briefing draft.

### 7.4 Hackathon demo scenario

1. The presenter frames the problem: "News tells you what happened, but this product shows how expectations were reassessed afterward."
2. The home dashboard shows the top 5 most-changed issues today.
3. They click into one representative issue.
4. The detail chart shows 24h/7d change and inflection-point markers.
5. They show the data summary card and interpretation-caution badge.
6. They explain the safeguard: "this is a data-based issue monitoring tool, not a prediction or a recommendation."

---

## 8. Functional Requirements

### 8.1 Home dashboard

#### Purpose

Let users see today's most-changed global issues as soon as they enter the service.

#### Requirements

- Show the top N issues by 24-hour change.
- Show issues with large 7-day change in a separate section or tab.
- Each issue card shows title, category, current expectation value, 24h change, 7d change, interpretation-caution badge, and data as-of timestamp.
- Issues with low activity or high volatility show a caution indicator on the card.
- On data load failure, show the last successful data and its as-of timestamp.

#### Acceptance criteria

- Users must be able to identify high-change issues within 10 seconds of the first screen.
- Each issue card must clearly show the direction and magnitude of change.
- Issues requiring interpretation caution must be visually distinguishable.

### 8.2 Sudden-change issue list

#### Purpose

Identify issues with large short-term changes in reflected expectation value.

#### Requirements

- Provide a list ranked by 24-hour change.
- Provide a list ranked by 7-day change.
- Show change magnitude in percentage points.
- Show absolute change magnitude and direction together.
- Issues below the activity threshold are either excluded from the default list or marked with a caution badge.

#### Acceptance criteria

- Users must be able to see at a glance which issues moved the most.
- Issues requiring interpretation caution due to low activity must be clearly marked.

### 8.3 Issue detail screen

#### Purpose

Provide an issue's change flow and interpretation-caution factors on a single screen.

#### Requirements

- Provide the issue title and a brief description.
- Show the current reflected expectation value.
- Show 24h, 7d, and (if possible) 30d change.
- Provide a time-series chart.
- Show simple inflection-point markers.
- v3 provides manually entered related event candidates for representative
  issues. The approved v4 path provides only verified candidates tied to a
  change episode and stored citation sources.
- Provide a template-based data summary.
- Provide an interpretation-caution badge.
- Show the source data's as-of time.

#### Acceptance criteria

- Users must be able to understand when, how much, and in which direction the issue changed.
- Related events must be presented as candidates, not asserted as causes.
- The interpretation-caution badge must be clearly visible near the top of the detail screen or around the chart.

### 8.4 Time-series chart

#### Purpose

Visually present the change in reflected expectation value per issue.

#### Requirements

- Provide 24-hour and 7-day window selection by default.
- Provide a 30-day window if data is available.
- Show the change trend in reflected expectation value as a line chart.
- Show markers at major inflection points.
- Let users hover or tap a point in time to see the value and change at that point.
- Provide interpretation-caution text below the chart.

#### Acceptance criteria

- Users must be able to understand the recent direction of change from the chart alone.
- Guidance on the scope of data interpretation must appear around the chart.

### 8.5 Change calculation

#### Purpose

Provide an intuitive comparison of short-term and weekly changes in reflected expectation value.

#### Formula

```text
24h change = current reflected expectation value - reflected expectation value 24 hours ago
7d change = current reflected expectation value - reflected expectation value 7 days ago
Absolute change = abs(current reflected expectation value - reflected expectation value at reference time)
```

#### Requirements

- Show change in percentage points (pp).
- Distinguish increases and decreases by color and sign.
- If there is no data at the past reference point, show "insufficient data."
- Include the calculation reference time in both the API response and the screen.

### 8.6 Simple inflection-point display

#### Purpose

Let users quickly identify when a change began or intensified.

#### Requirements

- Automatically detect segments where change exceeds a set threshold.
- Hackathon default: +-5pp change within an adjacent segment or short window.
- Show inflection-point markers on the chart.
- Clicking or hovering an inflection point shows the change before and after that point.
- Do not assert a cause for the inflection point.

#### Acceptance criteria

- Users must be able to quickly identify an issue's major change points.
- Inflection-point explanations must be distinguished between "observed change" and "related event candidate."

### 8.7 Interpretation-caution badge

#### Purpose

Prevent overinterpretation caused by low activity, high volatility, or insufficient data.

#### Badge types

| Badge | Example criteria | User guidance |
|---|---|---|
| Data sufficient | Data points and activity level above threshold | Can be referenced as a relatively continuous trend. |
| Activity caution | Activity level or volume below threshold | Interpret the change with caution. |
| Sudden-change caution | Large short-term change and high volatility | May be a temporary reaction; further verification is needed. |
| Insufficient data | Insufficient past reference point or time-series data points | Trend interpretation has limitations. |

#### Requirements

- Apply the same badge system to issue cards and the detail screen.
- Express badges as "interpretation caution," not "trust level."
- Manage badge criteria consistently between frontend and backend/API documentation.

### 8.8 Template-based data summary

#### Purpose

Reduce the time users need to interpret numbers and charts.

#### Requirements

- Provide a numeric, template-based summary by default instead of free-form AI analysis.
- Limit the summary to 3-5 sentences.
- The summary must include the time window, direction of change, change magnitude, inflection point, and interpretation caution.
- Even where an LLM is used, use it only to polish the template's output wording, not as the primary content source.
- Prohibit asserting causes, asserting outcomes, or recommending actions.

#### Default template

```text
This issue concerns [issue description].
Over the past [time window], the reflected expectation value in public data has [risen/fallen], with a change of [value]%p.
The largest change was observed around [time].
[Related event candidate] is a context candidate that can be checked around that time.
However, interpretation requires caution due to [activity level/volatility/insufficient data].
```

### 8.9 Context candidates

#### Purpose

Help users understand the context around an inflection point.

#### Frozen hackathon v3 approach

- Do not implement automated context matching in v3.
- Provide manually entered event candidates limited to 3-5 representative issues.
- Present event candidates as "context that can be checked alongside the change," not as "the cause."
- For issues with no events, hide the event section or show "no related event candidate."

#### Acceptance criteria

- Related events must not read as the cause of the change.
- In the demo, connect event candidates to at least one representative issue.

#### Approved post-MVP v4 extension (TASK-056~065)

- Research may run only for bounded change episodes selected by signal, absolute
  change, heat, or staleness rules.
- Only URLs in OpenRouter API `url_citation` annotations are evidence. A URL in
  model text is ignored.
- A candidate is public only when deterministic provenance/date/entity/source
  gates and an independent verifier model pass. All other states fail closed.
- One official source that directly supports the tracked condition, or two
  independent sources supporting the same event and date, is required.
- Timing is displayed as comparable context, never as a relationship or cause.
- No verified candidate means `context_summary=null` and the context section is
  hidden; candidate absence is not an error.
- Every public context sentence references a stored verified-candidate ID and
  every metric sentence references a stored metric ID.
- Deployment and production-database writes remain outside this extension.

### 8.10 Data as-of timestamp and disclaimer text

#### Requirements

- Show the data as-of timestamp on the home dashboard, issue cards, detail screen, and around the chart.
- Show interpretation-caution text on every major data screen.
- On data collection failure, show the last successful collection time.

#### Default text

```text
This indicator reflects the changing expectations of participants in Polymarket's public prediction market. It does not represent the judgment of the public at large, and interpretation requires caution depending on data activity level and volatility.
```

---
