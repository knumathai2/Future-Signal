# PRD: Data, UX, Success Metrics, Team, Schedule

_Source: former project-root PRD sections 9-14._

---

## 9. Data Requirements

### 9.1 Data sources

Initial data draws on Polymarket's public market data. The product collects and processes market information, category/tags, reflected expectation values, activity level, liquidity, and time-series change data as they appear in public data.

The hackathon MVP does not automatically collect external news/event information. For representative demo issues only, manually entered event candidates may be used.

### 9.2 Data to collect

| Data | Purpose | Required for MVP |
|---|---|---|
| Market ID | API connection and detail lookup | Required |
| Issue title | Displayed to users | Required |
| Issue description | Supports context understanding | Required |
| Category / tags | Filtering and classification | Required if feasible |
| Current reflected expectation value | Shows current state | Required |
| Past reflected expectation value | Change calculation | Required |
| Price history | Time-series chart | Required |
| 24h change | Sudden-change detection | Required |
| 7d change | Weekly change detection | Required |
| Activity level / volume | Interpretation-caution badge | Required |
| Liquidity | Reference for data stability | Required if feasible |
| Update timestamp | Trust and freshness display | Required |
| Related event candidates | Representative-issue demo | Optional |

### 9.3 Analysis elements

| Analysis element | Analysis purpose | Display method | Interpretation risk |
|---|---|---|---|
| Change in reflected expectation value | Identify direction of change | Current value, vs. yesterday, vs. last week | Could be read the same as the actual probability of an outcome |
| 24h change | Detect short-term sudden change | "24h +8.2%p" format | A temporary reaction may be misread as a structural change |
| 7d change | Identify recent trend change | Weekly change chart | The impact of a single event may be overweighted |
| Activity level | Supports data interpretation | Activity-level caution badge | Activity level does not fully represent level of interest |
| Liquidity | Reference for indicator stability | Interpretation-caution criterion | Change magnitude may look larger under low liquidity |
| Volatility | Check the degree of indicator fluctuation | Sudden-change caution badge | High volatility does not necessarily mean high importance |
| Inflection point | Identify the timing of change | Chart marker | Risk of being asserted as a cause |
| Category | Browsing convenience | Filter or label | May be distorted depending on classification quality |

### 9.4 Data scope limits

| Item | Standard |
|---|---|
| Initial market count | 30-50 |
| Market status | Primarily active |
| Market type | Primarily binary |
| Excluded | Insufficient data points, extremely low activity, multi-outcome markets that are hard to interpret |
| Refresh cycle | Manual refresh or limited scheduling for the hackathon |
| Demo fallback | Prepared static JSON/CSV dataset |

### 9.5 Data-labeling principles

- Do not describe data as "the opinion of the public at large."
- Describe it as "the flow of Polymarket participants' judgment."
- Describe it as "expectation change reflected in public prediction-market data."
- Describe it as a "related event candidate," not "the cause."
- Always show a caution notice for issues with low activity or high volatility.
- Never omit the data as-of timestamp.

---

## 10. UX / Information Architecture

### 10.1 Main hackathon MVP screens

| Screen | MVP inclusion | Description |
|---|---|---|
| Home dashboard | P0 | Today's most-changed issue cards and 24h/7d lists |
| Issue detail screen | P0 | Chart, change summary, badge, data as-of timestamp |
| Category filter | P1 | Provided if source tags or manual mapping are available |
| Activity-based list | P1 | Provided as a supplementary list if data is available |
| Saved issues screen | Excluded | Post-Phase 2 |
| Weekly summary screen | Excluded | Post-Phase 3 |
| Team sharing screen | Excluded | B2B expansion direction |

### 10.2 Home dashboard composition

| Area | Content |
|---|---|
| Top summary | Data as-of timestamp, number of markets collected, interpretation guidance |
| Sudden-change issues | Top issue cards by 24-hour change |
| Weekly-change issues | Top issue cards by 7-day change |
| Category filter | P1 feature |
| Interpretation guidance | Notice on data representativeness and interpretation caution |

### 10.3 Issue card composition

Each issue card includes:

- Issue title
- Category or tags
- Current reflected expectation value
- 24h change
- 7d change
- Mini chart or direction indicator
- Interpretation-caution badge
- Data as-of timestamp

### 10.4 Issue detail screen composition

| Area | Content |
|---|---|
| Header | Issue title, category, current reflected expectation value |
| Change summary | 24h, 7d, and (if possible) 30d change |
| Time-series chart | Window selector, inflection-point markers, tooltip |
| Data summary card | Recent change, observed inflection point, interpretation caution |
| Related event candidates | Manually entered candidates, limited to representative issues |
| Interpretation caution | Activity-level, volatility, and insufficient-data badges |
| Reference time | Source data collection and calculation reference time |

### 10.5 UX copy principles

Recommended wording:

- "A shift in outlook has been observed."
- "The reflected expectation value has risen, according to public data."
- "A change has appeared in Polymarket participant data."
- "You can check this alongside related event candidates."
- "Activity is low, so interpretation requires caution."

Prohibited wording:

- Language that states a specific outcome with certainty
- Language that encourages a specific action
- Language that asserts something as the judgment of the public at large
- Language that asserts a cause of change with certainty
- Language that overstates accuracy
- Language implying betting, investment, profit, recommendation, or signal

---

## 11. Differentiation Strategy

### 11.1 Difference from news

News centers its explanation on the occurrence of an event. Outlook Signals shows how the expectation reflected in public prediction-market data moved after the event.

### 11.2 Difference from social media / communities

Social media and communities react quickly but mix signal with noise. Outlook Signals organizes issues around the quantitative change and time-series flow of public prediction-market data.

### 11.3 Difference from research reports

Research reports have depth but update slowly. Outlook Signals is well-suited to daily monitoring because it repeatedly tracks each issue's change magnitude and inflection points.

### 11.4 Difference from simple data display

| Interpretation layer | Description | MVP inclusion |
|---|---|---|
| Change ranking | Selects today's most-changed issues | P0 |
| Change context | Summarizes when, how much, and in which direction an indicator moved | P0 |
| Inflection-point detection | Marks important change points in the time series | P0 |
| Interpretation-caution badge | Caution indicator based on activity level, liquidity, volatility | P0 |
| Event-candidate linking | Manually linked, limited to representative issues | P1 |
| Content-creation tools | Chart image export, etc. | Excluded |

---

## 12. Success Metrics

### 12.1 Hackathon MVP success criteria

| Metric | Target |
|---|---|
| Demo completion | The flow of home dashboard -> detail screen -> chart -> summary card runs without interruption |
| Data coverage | 30+ active binary markets displayed |
| Change calculation | 24h/7d change shown on each issue card |
| Detail chart | Time-series chart shown for 3+ representative issues |
| Interpretation caution | Badge or guidance text shown on every major screen |
| Fallback readiness | Static-JSON-based demo possible if the API fails |
| Presentation clarity | Judges understand it as "an issue monitoring tool, not a prediction service" |

### 12.2 Post-MVP validation metrics

| Metric | Purpose | Example target |
|---|---|---|
| Detail click-through rate after first visit | Validate dashboard usefulness | 40%+ |
| Average issue detail views per session | Validate exploration value | 3+ |
| Return visit rate | Validate daily-monitoring value | 25%+ within 7 days |
| Summary-card satisfaction | Validate interpretation-layer quality | 70%+ positive response |
| Interpretation-caution badge awareness | Validate that the trust safeguard lands | 80%+ awareness in user interviews |
| Content-material usage rate | Validate value for content creators | 50%+ of interviewees find it useful |

### 12.3 Qualitative validation questions

- Did users find issues worth covering faster through this product?
- Did the chart and summary help users understand the issue?
- Did users avoid overreading the reflected expectation value as an actual likelihood of the outcome?
- Did content creators feel they could use this for finding content material?
- Did researchers and planners feel they could use this to draft briefings?
- Did the interpretation-caution text increase trust in the product?

---

## 13. Team Roles (4 people)

| Role | Core work | Deliverables | Bottleneck risk |
|---|---|---|---|
| PM / planning / presentation | Problem definition, MVP scope management, wording policy, presentation story, demo scenario | Presentation deck, screen copy, QA checklist | Failure to control scope |
| Frontend / UI | Dashboard, card UI, detail screen, chart, responsive UI | Web MVP screens | Needs dummy data if the API is delayed |
| Backend / API / DB | Data storage, API design, ranking API, detail API, caching | API server, DB schema | Dependent on the data collection structure |
| Data / AI / visualization logic | Polymarket data collection, normalization, change calculation, inflection points, template summary | Sample dataset, analysis logic | Data-structure complexity |

### 13.1 Role operating principles

1. Frontend develops in parallel from Day 1 using dummy JSON.
2. Backend and the data owner finalize the API contract and sample data first on Day 1.
3. PM acts as the scope controller managing feature-addition requests.
4. If real data integration is delayed, switch to a static-JSON-based demo.

---

## 14. 5-Day Development Schedule

### Day 1: Finalize scope + validate data + screen skeleton

| Role | Work |
|---|---|
| PM | Finalize MVP scope, define prohibited wording, draft presentation story |
| Frontend | Wireframe dashboard/detail screens, start UI with dummy JSON |
| Backend | DB schema, define API contract, set up server project |
| Data/AI | Confirm Polymarket data structure, collect 10 sample markets |

Deliverables:

- Screen structure
- API contract document
- Sample data
- MVP scope document
- Draft presentation key messages

### Day 2: Data pipeline + core UI implementation

| Role | Work |
|---|---|
| PM | Organize user scenarios, prepare Q&A for the judging panel |
| Frontend | Build home dashboard, issue cards, ranking UI |
| Backend | Build market-list API, ranking API |
| Data/AI | Calculate 24h/7d change, normalize 30-50 samples |

Deliverables:

- Dashboard v1
- Ranking API
- Change-calculation data
- Candidate issue list for the demo

### Day 3: Detail screen + chart + badges

| Role | Work |
|---|---|
| PM | Interpretation-caution text, disclaimer text, terminology revisions |
| Frontend | Build detail screen, time-series chart, tooltip |
| Backend | Connect issue-detail API, price-history API |
| Data/AI | Inflection-point threshold logic, interpretation-caution badge logic |

Deliverables:

- Issue detail screen
- Time-series chart
- Inflection-point markers
- Interpretation-caution badge

### Day 4: Summary feature + complete the demo flow

| Role | Work |
|---|---|
| PM | Draft presentation deck, write demo script |
| Frontend | UI polish, handle empty/loading/error states |
| Backend | Stabilize API, handle fallback data |
| Data/AI | Generate template summaries, link manual event candidates |

Deliverables:

- Template summaries
- 3 representative issues for the presentation
- Stabilized demo flow
- Presentation deck 70% complete

### Day 5: Integration QA + finalize presentation

| Role | Work |
|---|---|
| PM | Finalize presentation deck, prepare risk-response explanations, finalize demo script |
| Frontend | Polish demo screens, check responsiveness |
| Backend | Deploy, prepare dummy fallback for API outage |
| Data/AI | Check data errors, reinforce representative examples |

Deliverables:

- Deployed MVP
- Presentation deck
- Demo scenario
- Backup video or screen captures
- Q&A response sheet

---
