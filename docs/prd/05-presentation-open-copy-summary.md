# PRD: Presentation, Open Issues, Initial Copy, Summary

_Source: former project-root PRD sections 19-22._

---

## 19. Hackathon Presentation Strategy

### 19.1 Core presentation message

This service is not a tool for guessing the future. It visualizes the change in expectation reflected in public prediction-market data, helping users quickly understand how complex global issues are being reassessed.

### 19.2 Recommended presentation flow

1. Problem statement: There are many global issues, and news alone makes it hard to gauge the intensity of change.
2. Limits of existing approaches: News is event-centric, social media is noisy, reports are slow.
3. Solution idea: Show the change in expectation reflected in public prediction-market data as a time series.
4. Product demo: Check today's most-changed issues, view the detail chart, view the summary card, view the interpretation-caution badge.
5. Safeguards: Not representative of the public at large, no causal assertions, no action inducement, no participant tracking.
6. Growth potential: Content cards, saving, notifications, weekly reports, enterprise issue monitoring.

### 19.3 Points that improve award chances

| Point | Description |
|---|---|
| Problem definition | The problem of quickly grasping the flow of change in an age of information overload |
| Data differentiation | Uses public prediction-market data rather than news |
| Visualization impact | Charts and change magnitude are intuitive |
| Ethical safeguards | Designed to draw a clear line against betting/investment encouragement |
| MVP realism | Scope is realistically achievable and working within 5 days |
| Scalability | Can expand into content, research, and enterprise monitoring |

---

## 20. Open Issues

1. Need to confirm the detailed fields and update cycle of Polymarket's public data.
2. Need to finalize the access method and storage approach for price history.
3. Need to finalize the criteria for identifying binary markets.
4. Need to decide whether issue categorization will be based on source tags or manual mapping.
5. Need to decide whether issues below the activity threshold are excluded from the ranking or included with a caution indicator.
6. Need to decide whether the inflection-point threshold is fixed at +-5pp or adjusted per market volatility.
7. Need user testing to decide whether to fix the term "reflected expectation value" for use in the template summary.
8. Need to decide the criteria for selecting the 3 representative issues for the presentation demo.
9. Need to finalize the static-JSON fallback path for API failure.
10. Need to decide which of saving, notifications, or reports to expand first after the hackathon.

---

## 21. Initial Copy

### 21.1 Main copy

After the news, how did expectations move?

### 21.2 Sub copy

See at a glance how the reflected expectation value has changed for each issue, based on Polymarket's public prediction-market data.

### 21.3 Product description

Outlook AI Signals organizes, with data, the change in reflected expectation value, sudden-change moments, and interpretation-caution factors for major issues worldwide. It does not assert the future with certainty; instead, it presents the flow of judgment shown in public prediction-market data in an easy-to-understand way.

### 21.4 Feature-introduction copy

1. Check the global issues whose reflected expectation value has moved the most today.
2. Track how expectations were reassessed in public data after the news broke.
3. Quickly understand the flow of change in complex issues through charts and inflection points.
4. Check activity level and volatility together so you don't miss the limits of data interpretation.
5. Use numeric summary cards to quickly start your briefing or content draft.

---

## 22. Final Summary

Outlook AI Signals is not a service that asserts outcomes with certainty; it is an information-analysis dashboard for reading the flow of outlook change. The MVP, scoped for a 5-day hackathon and a 4-person team, focuses on the home dashboard, sudden-change issue ranking, issue detail chart, simple inflection points, interpretation-caution badge, template summary, and data as-of timestamp.

The current final assessment of this PRD is "B: buildable if the core scope is narrowed." The dashboard, change calculation, detail chart, interpretation-caution badge, and template summary can all be built to a genuinely working level within 5 days. On the other hand, automated news matching, free-form AI analysis, chart-image export, saved issues, notifications, weekly reports, and team sharing should be excluded from the hackathon MVP.

The most important product principles are neutrality, careful wording, and disclosure of data limitations. Polymarket's public data must not be presented as the opinion of the public at large; interpretation must be limited to "the flow of judgment among Polymarket participants" and "expectation change reflected in public prediction-market data."

At the hackathon, it will be more advantageous to present an MVP with "a clearly defined problem, a visible data-driven solution flow, and safeguards designed in" than one that simply has "a lot of technical features."
