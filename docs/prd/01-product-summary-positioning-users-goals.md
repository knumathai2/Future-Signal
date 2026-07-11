# PRD: Public Prediction-Market Data-Based Sudden-Issue Monitoring Dashboard

Document version: v1.1
Date: 2026-07-07
Document purpose: PRD for a 5-day hackathon submission and 4-person team MVP implementation
Product status: Concept -> Hackathon MVP planning stage
Working title: Outlook Signals
Final verdict: B - Buildable if the core scope is narrowed

---

## 1. Product Summary

### 1.1 One-line definition

Outlook Signals is an information-analysis dashboard that surfaces global issues whose reflected expectation values have recently shifted significantly in Polymarket's public prediction-market data, and helps users quickly understand how an issue is being reassessed through change magnitude, time-series charts, and interpretation-caution notices.

### 1.2 Rescoping direction

The earlier version of this PRD was closer to a "global issue outlook analysis platform." That scope is too broad for a 5-day hackathon with a 4-person team, so this revision redefines the product along the following lines:

1. Narrow the product scope to a "sudden-change issue monitoring demo MVP based on public prediction-market data."
2. Fix the core experience to: "check today's most-changed issues -> view the detail chart -> read the template summary and interpretation-caution notice."
3. Limit data scope to roughly 30-50 active binary markets.
4. Provide AI output as a numeric, template-based summary rather than free-form analysis.
5. Freeze the hackathon v3 path to 3-5 manually entered related-event candidates.
   The post-MVP TASK-056~065 v4 exception may surface only verified context
   candidates under ADR-038; it does not change the historical v3 scope.
6. Exclude saving, notifications, weekly reports, team sharing, and chart-image export from the hackathon MVP.

### 1.3 Core product concept

Users can learn about an event itself through mainstream news, but it's hard to tell how public prediction-market participants' expectations were reassessed after that event. Outlook Signals uses time-series changes in Polymarket's public data to show which issues have moved the most recently, along with each issue's change in reflected expectation value, inflection points, and interpretation-caution factors driven by activity level and volatility.

This product is not a tool for guessing future outcomes. It does not encourage choosing any particular outcome, and it does not present Polymarket data as the judgment of the public at large. Language throughout the product is limited to phrases such as "expectation change reflected in public prediction-market data," "movement observed in Polymarket participant data," and "related event candidate."

### 1.4 Hackathon success principles

| Principle | Description |
|---|---|
| Cut features, sharpen the demo flow | Focus on the flow of seeing changed issues on the first screen, then checking the chart and summary in detail. |
| Limit data, raise visualization quality | Rather than covering every market, reliably show 30-50 binary markets. |
| Don't let AI overstate | Default to numeric, template-based summaries instead of free-form LLM analysis. |
| Avoid automated causal inference | Don't auto-link news to changes in a way that implies causation. |
| Build safeguards into the screens | Keep interpretation-caution badges, data as-of timestamps, and disclaimer text visible on the main screens at all times. |

---

## 2. Background and Problem Definition

### 2.1 Background

Global political, economic, technological, policy, and social issues change quickly. Users can confirm an event through the news, but it's difficult to independently figure out how much, and in which direction, market participants' expectations shifted after that event.

News centers on the event itself; social media and communities react quickly but mix signal with noise; expert reports have depth but update slowly; general search requires users to connect the context themselves.

Polymarket's public prediction-market data leaves a time series of how participants' expectations about a specific issue changed, which makes it usable as supplementary data for issue monitoring. However, since this data does not represent the public at large, the product must apply careful language and interpretation-caution safeguards throughout.

### 2.2 Problem users face

Users have to check multiple information sources at once to understand the flow of change around a major issue. Because information is fragmented, it's hard to grasp the direction and intensity of change at a glance.

News tells you "what happened," but not "how expectations were reassessed afterward." Social media reacts quickly but mixes emotional reaction and exaggerated interpretation, making it hard to isolate a real judgment signal. Reports are more trustworthy but limited in tracking real-time change.

### 2.3 Core problem statement

Users want to quickly understand how expectations are changing around global issues, but information today is fragmented across news, social media, and reports, making it hard to grasp the direction and intensity of change at a glance.

---

## 3. Product Positioning

### 3.1 What the product does

1. Selects global issues with large recent changes in reflected expectation value from public prediction-market data.
2. Calculates 24-hour and 7-day changes in reflected expectation value per issue.
3. Provides a time-series chart and simple inflection-point markers on the detail screen.
4. Displays an interpretation-caution badge based on activity level, volatility, and insufficient data points.
5. Provides a short, numeric, template-based summary describing the change.
6. Displays the data as-of timestamp and interpretation-caution text on every major screen.

### 3.2 What the product does not do

1. Does not assert future outcomes with certainty.
2. Does not encourage choosing a particular outcome.
3. Does not track any specific participant's or account's activity.
4. Does not assert a cause of change. Automated v4 context may compare timing
   only after citation provenance, deterministic hard gates, and independent
   verification pass.
5. Does not present Polymarket participants' judgment as the judgment of the public at large.
6. Does not provide action-inducing CTAs, performance-based rankings, or features that push users toward external platforms.
7. In the hackathon MVP, does not provide login, saving, notifications, weekly reports, or team sharing.

### 3.3 Central statement for presentation and product description

News tells you "what happened." Outlook Signals shows you "how expectations, as reflected in public prediction-market data, were reassessed afterward."

### 3.4 Prohibited vs. replacement wording

| Wording to avoid | Replacement wording |
|---|---|
| We predict the future | We show how expectations are changing |
| The likelihood has increased | The reflected expectation value has risen in public data |
| Here's what people think | Change observed in Polymarket participant data |
| Investment signal | Issue-change observation indicator |
| Recommended issue | Exploration list ranked by change magnitude |
| Trust badge | Interpretation-caution badge |
| Cause analysis | Related event candidate |
| buy, bet, trade, odds, profit, position, signal, recommendation | Not used |

---

## 4. Target Users

### 4.1 MVP primary target 1: Content creators

#### Problem the user faces

Content creators have many issues to cover each day but find it hard to identify which ones actually moved significantly. News alone doesn't explain how much expectations shifted after an event.

#### Why they use the product

Being able to check today's most-changed issues, per-issue charts, change summaries, and interpretation-caution text in one place cuts down the time needed to find content material and draft an explanation.

#### Key usage contexts

- Before writing a newsletter
- Before planning YouTube/Shorts content
- When finding material for blogs, Brunch, or LinkedIn posts
- When producing daily briefing content

### 4.2 MVP primary target 2: Researchers / planners / strategy staff

#### Problem the user faces

Researchers and strategy staff need to track global issues repeatedly, but it's hard to see the intensity and timing of change quantitatively. Checking and interpreting multiple sources directly takes a lot of time.

#### Why they use the product

Being able to check per-issue changes in reflected expectation value, inflection points, and interpretation-caution markers on one screen makes it a useful starting point for briefings and research.

#### Key usage contexts

- Preliminary exploration before writing a weekly report
- Preparing for strategy meetings
- Monitoring policy/regulatory issues
- Analyzing the impact of global events

### 4.3 User from the hackathon judging perspective

For the hackathon demo, the representative user is "a knowledge worker who needs to quickly understand a complex global issue." To help judges grasp the product's value within a minute, the dashboard flow centers on checking sudden-change issues and then viewing the detail chart.

---

## 5. Goals and Non-Goals

### 5.1 Product goals

1. Help users quickly understand the flow of expectation change per issue as reflected in public prediction-market data.
2. Automatically surface global issues with large changes today.
3. Provide time-series change and simple inflection points for each issue on a single screen.
4. Clearly display activity-level and volatility limitations to prevent overinterpretation.
5. Provide summaries that content creators and researchers can use as a starting point for briefings, content, and research.
6. Complete a genuinely working web MVP within the 5-day hackathon.

### 5.2 Product non-goals

1. Does not cover every Polymarket market.
2. Does not fully support multi-outcome markets.
3. Does not treat real-time data refresh as a core requirement.
4. The frozen hackathon v3 does not implement automated context matching. The
   approved post-MVP v4 program is limited to ADR-038's verified, fail-closed
   context-candidate path.
5. Does not offer free-form AI analysis as a core feature.
6. Does not implement login-based saving, notifications, report generation, or team sharing.
7. Does not imply a specific outcome choice, external action, or profit potential.

---
