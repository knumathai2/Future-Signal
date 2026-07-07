# PRD: Risks, Technical Requirements, Operations, Release

_Source: former project-root PRD sections 15-18._

---

## 15. Risks and Mitigation

### 15.1 Implementation risk

| Item | Content |
|---|---|
| Risk | Trying to build the dashboard, chart, API, data collection, and summary all at once could reduce overall polish. |
| Likelihood | High |
| Impact | High |
| Mitigation | Fix only P0 features; clearly deprioritize P1/P2. |
| Hackathon fallback | Frontend develops first with dummy JSON; if real data integration is delayed, connect only 10 representative issues. |

### 15.2 Data collection risk

| Item | Content |
|---|---|
| Risk | Polymarket's data structure is complex, and handling price history or outcomes may take longer than expected. |
| Likelihood | Medium-High |
| Impact | High |
| Mitigation | Limit scope to binary markets and collect only 30-50 active markets. |
| Hackathon fallback | Use a pre-collected JSON/CSV; present real-time collection only at the level of a refresh button. |

### 15.3 AI-analysis accuracy risk

| Item | Content |
|---|---|
| Risk | AI may assert a cause of change or generate overstated language. |
| Likelihood | High |
| Impact | High |
| Mitigation | Restrict free-form AI summaries; use numeric, template-based summaries. |
| Hackathon fallback | Call it a "data summary card" instead of an "AI summary," and use the LLM only optionally. |

### 15.4 Legal, ethical, and product-framing risk

| Item | Content |
|---|---|
| Risk | Given the nature of Polymarket data, the product could be misread as a betting, gambling, or investment-signal service. |
| Likelihood | High |
| Impact | Very high |
| Mitigation | Prohibit wording such as buy, bet, trade, odds, profit, position, signal, recommendation. |
| Hackathon fallback | Fix the product positioning as "outlook-change monitoring" and show interpretation-caution text on every screen. |

### 15.5 Presentation-quality risk

| Item | Content |
|---|---|
| Risk | If the explanation drifts toward data/technology, judges may struggle to see the user value. |
| Likelihood | Medium |
| Impact | High |
| Mitigation | Structure the presentation around the story "news tells you what happened, but we show how expectations were reassessed afterward." |
| Hackathon fallback | Build a demo scenario that follows one representative issue all the way through. |

### 15.6 Team bottleneck risk

| Item | Content |
|---|---|
| Risk | If the data owner gets stuck, backend and frontend work can be delayed together. |
| Likelihood | High |
| Impact | High |
| Mitigation | Finalize the dummy data schema on Day 1 so frontend and backend can work in parallel. |
| Hackathon fallback | Switch to a static-JSON-based demo if real API integration fails. |

---

## 16. Technical Requirements

### 16.1 Frontend

- Responsive web first
- Home dashboard card UI
- 24h/7d ranking tabs or sections
- Issue detail page
- Time-series chart rendering
- Inflection-point markers and tooltips
- Interpretation-caution badges
- Loading, empty, and error states
- Data as-of timestamp display

### 16.2 Backend

- Public data collection or manual-refresh endpoint
- Issue normalization logic
- Change-calculation logic
- Threshold-based inflection-point detection logic
- Badge derivation based on activity level, volatility, and data insufficiency
- Template-summary generation logic
- Caching and storage of the last good data

### 16.3 Recommended APIs

| API | Description |
|---|---|
| `GET /api/issues` | Issue list, card data |
| `GET /api/issues/ranking?window=24h` | 24-hour change ranking |
| `GET /api/issues/ranking?window=7d` | 7-day change ranking |
| `GET /api/issues/:id` | Issue detail data |
| `GET /api/issues/:id/history?window=7d` | Time-series data |
| `POST /api/refresh` | Manual data refresh for the hackathon |

### 16.4 Data pipeline

1. Collect public data
2. Filter, focused on binary markets
3. Normalize issues and categories
4. Store time-series data or cache as JSON
5. Calculate 24h/7d change
6. Detect inflection points based on threshold
7. Generate badges based on activity level, volatility, and data insufficiency
8. Generate template summaries
9. Serve the dashboard API

### 16.5 Non-functional requirements

| Item | Requirement |
|---|---|
| Performance | Target initial home-dashboard load under 3 seconds |
| Updates | Manual refresh or limited-cycle updates for the hackathon |
| Reliability | On data collection failure, show the last good data and its as-of timestamp |
| Transparency | Show a data as-of timestamp on every key metric |
| Scalability | Design the data structure to accommodate growth in categories and issue count |
| Safety | Apply wording policy and interpretation-caution display throughout the product |

---

## 17. Operations and Policy Guide

### 17.1 Default in-screen notice

Show the following notice on every major data screen:

```text
This indicator reflects the changing expectations of participants in Polymarket's public prediction market. It does not represent the judgment of the public at large, and interpretation requires caution depending on data activity level and volatility.
```

### 17.2 Issue detail screen caution text

```text
The change shown below is a flow observed in public data. Related events are offered as candidates to aid contextual understanding and do not assert a cause of the change.
```

### 17.3 Prohibited UX patterns

- Buttons that emphasize choosing a specific outcome
- CTAs that encourage external action
- Rankings that imply performance
- Activity tracking centered on a specific participant
- Definitive outcome statements
- Exaggerated language such as "guaranteed," "certain," or "definitely"
- Language implying investment, betting, profit, recommendation, or signal

---

## 18. Release Plan

### 18.1 Hackathon MVP

Goal: Let users check today's most-changed issues and view the detail flow.

Key work:

- Collect 30-50 active binary markets
- Calculate 24h/7d change
- Build the home dashboard
- Build the sudden-change issue ranking
- Build the issue detail screen
- Build the time-series chart
- Build simple inflection-point markers
- Build the interpretation-caution badge
- Build the template summary
- Prepare 3 representative issues for the demo

Deliverables:

- Web MVP
- Sample dataset
- Presentation demo scenario
- Q&A response sheet

### 18.2 Phase 2: Content-creator features

Goal: Let content creators use the product in their actual workflow.

Key work:

- Chart image export
- Issue-description card generation
- Saved issues
- Automatic inclusion of source/caution text for sharing
- Improvements based on content-creator interviews

### 18.3 Phase 3: Repeat usage and B2B features

Goal: Validate return usage and monetization potential.

Key work:

- Change notifications
- Weekly report generation
- Team sharing
- PDF export
- User-configurable category interests
- Enterprise issue-monitoring dashboard

---
