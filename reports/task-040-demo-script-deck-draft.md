# TASK-040: Day 4 Demo Script and Deck Draft

## Context Checked

- `AGENTS.md`
- PRD section files under `docs/prd/`
- UX copy and safety guidance under `docs/ux-design/`
- Service Design AI output and participant policy sections
- Technical Design metrics, detection, and report architecture sections
- `memory/project.md`
- `memory/session.md`
- `tasks/active.md`
- `prompts/planning.md`
- `reports/day-4-work-allocation.md`
- `standards.md`
- `memory/glossary.md`
- Current frontend/backend surfaces for dashboard, detail, chart, report card,
  information notice, static fallback, and related-event seed data

Current implementation assumptions:

- Current branch baseline is `origin/main` at `d9f61c3`, which includes
  `TASK-043` v2 issue-explainer report shape.
- This branch includes the dashboard, detail screen, chart windows, caution
  badges, data-as-of timestamps, report-card states, information notice, and
  manually curated related-event seed path.
- This branch does not include later branch-only Korean issue-display or broad
  Korean category-filter work unless it is separately merged later. The deck
  draft therefore avoids claiming those as confirmed in this branch.
- Live/local data can be shown through the FastAPI API when configured; static
  fallback data is available with honest data-as-of timing when live data is not
  available.

## Deck Outline

| Slide | Title | Purpose | Key speaking point | Visual needed |
|---|---|---|---|---|
| 1 | Outlook Signals | Establish the product frame | "뉴스 이후, 공개 데이터에 반영된 기대값이 어떻게 다시 읽혔는지 보여주는 이슈 관찰 대시보드입니다." | Product name over dashboard screenshot |
| 2 | Problem | Explain the user pain | Global issues move quickly, but news is event-centered, social feeds are noisy, and reports update slowly. Users need a faster way to see which issues deserve closer reading. | Three-column contrast: news, social feeds, reports |
| 3 | Core Idea | Show the data differentiation | Use public Polymarket data as an additional observation layer: not a public opinion measure, but a time-series view of participant reassessment. | Simple flow: public data -> metrics -> issue cards |
| 4 | MVP Flow | Anchor the build scope | The MVP flow is intentionally narrow: Home -> Detail -> Chart -> Summary -> caution notice -> manual context candidate. | Six-step storyboard with screenshots |
| 5 | Home Dashboard | Show first-screen value | The home screen ranks issues by recent observed change, while keeping data-as-of timing and interpretation caution near the numbers. | Home screenshot with one issue card highlighted |
| 6 | Detail and Chart | Show analytical depth | The detail screen combines current reflected value, 24h/7d/30d movement, a line chart, and 5pp threshold markers without asserting causes. | Detail header and chart screenshot |
| 7 | Issue Summary | Show interpretation support | The v2 summary is fixed-section issue explanation: meaning, current reading, conditional scenario sections, checkpoints, and caution. | Report card screenshot |
| 8 | Safeguards | Make trust boundary explicit | The product stays aggregate-only, manually labels context candidates, keeps data-as-of timing visible, and stores only safety-filtered report output. | Safety checklist slide |
| 9 | Built in 5 Days | Prove implementation realism | Frontend, backend, data pipeline, threshold detection, report generation, and fallback behavior are working MVP pieces, not just mockups. | Architecture strip: collector -> DB -> API -> React |
| 10 | Day 5 Finish | Set the final runbook | Day 5 focuses on screenshot capture, live/local readiness check, final wording pass, rehearsal, and backup path. | Checklist slide |

## Demo Script

Target length: 3-5 minutes.

| Time | Screen/action cue | Presenter narration | Safety/caution cue |
|---|---|---|---|
| 0:00-0:25 | Open Home | "Outlook Signals는 글로벌 이슈를 하나씩 검색하게 만드는 대신, 최근 공개 데이터에 반영된 기대값 변화가 큰 이슈를 먼저 보여줍니다. 사용자는 오늘 어떤 이슈가 다시 읽히고 있는지 첫 화면에서 확인할 수 있습니다." | Mention that the list is an exploration list by observed change, not a public-opinion ranking. |
| 0:25-0:55 | Point to issue cards | "각 카드에는 현재 기대값, 24시간과 7일 관측 변화, 데이터 기준 시각, 해석 주의 상태가 함께 붙어 있습니다. 숫자만 크게 보여주는 화면이 아니라, 숫자를 어떻게 조심해서 읽어야 하는지도 같은 화면에 둡니다." | Point to data-as-of timestamp and caution badge before opening detail. |
| 0:55-1:15 | Click one representative issue | "이제 변화가 큰 이슈 하나를 열어 보겠습니다. 데모에서는 관련 사건 후보가 등록된 이슈를 선택해 전체 흐름을 보여줍니다." | If selected issue has no candidate, use fallback line from the fallback section. |
| 1:15-1:55 | Detail header and metric tiles | "상세 화면에서는 이슈 설명, 현재 공개 데이터 기대값, 24시간/7일/30일 관측 변화를 한 화면에서 봅니다. 여기서도 데이터 기준 시각과 해석 주의 문구가 숫자 가까이에 유지됩니다." | Say that the value is observed in Polymarket participant data and is not a confirmed real-world result. |
| 1:55-2:35 | Chart window and marker | "차트는 24시간, 7일, 30일 창으로 볼 수 있고, 큰 변화 구간에는 5pp 기준선 통과 표시가 나타납니다. 이 표시는 변화 시점을 빨리 찾기 위한 장치이며, 원인을 단정하지 않습니다." | Point to the chart notice below the window selector. |
| 2:35-3:15 | Summary card | "아래 요약은 자유 형식 해설이 아니라 고정된 섹션 구조입니다. 이슈의 의미, 왜 살펴볼 만한지, 현재 데이터 흐름, 조건부 전개, 확인할 지점, 해석 주의가 정해진 틀로 저장됩니다." | If stored summary is absent, explain that the empty state is intentional and the chart/detail still remain usable. |
| 3:15-3:40 | Caution notice and full information note | "요약 아래에도 같은 해석 주의가 반복됩니다. 사용자가 숫자나 문장을 따로 떼어 읽지 않도록, 중요한 데이터 화면마다 안내를 붙였습니다." | Open the full information notice if time allows. |
| 3:40-4:10 | Manual context candidate section | "마지막으로 관련 사건 후보입니다. 이 항목은 자동 연결이 아니라 수동 입력한 맥락 후보입니다. 관측 변화와 함께 확인할 자료일 뿐, 변화의 원인으로 제시하지 않습니다." | Use the phrase "candidate, not cause" only if presenting in English; otherwise keep the Korean wording above. |
| 4:10-4:40 | Return to Home | "이렇게 홈에서 변화가 큰 이슈를 찾고, 상세 화면에서 차트와 요약, 해석 주의, 맥락 후보를 확인하는 것이 Day 4 MVP의 완성된 데모 흐름입니다." | Close with issue-monitoring framing. |

## Fallback Narration

### Backend or API unavailable

"현재 화면은 로컬 백업 데이터를 표시하고 있습니다. 이 경우에도 데이터 기준
시각을 그대로 보여주며, 최신 수집이 된 것처럼 말하지 않습니다. 데모의 핵심은
동일합니다. 홈에서 이슈를 고르고, 상세 차트와 요약 영역, 해석 주의 문구를
확인합니다."

### Stored report unavailable

"이 이슈에는 아직 저장된 템플릿 요약이 없을 수 있습니다. 이 상태도 의도된
화면입니다. 이슈 정보와 차트는 계속 확인할 수 있고, 저장 요약이 준비되면 같은
위치에 고정된 섹션 구조로 표시됩니다."

### Chart history insufficient

"선택한 기간의 기준 데이터가 충분하지 않으면 변화값을 억지로 채우지 않습니다.
대신 이력 부족 상태를 보여주고, 해석에 제한이 있음을 같은 화면에서 알립니다."

### Related-event candidate unavailable

"모든 이슈에 관련 사건 후보가 있는 것은 아닙니다. 후보가 없는 경우에는 빈
상태를 그대로 보여주며, 자동으로 외부 뉴스를 연결하지 않습니다. 데모 전체를
보여줄 때는 수동 후보가 등록된 대표 이슈를 선택합니다."

## Screenshot and Rehearsal Checklist

Required screenshots:

- Home dashboard with top issue cards, data-as-of timestamp, and caution badge.
- A representative issue card before click.
- Detail header with reflected expectation value and metric tiles.
- Chart section with selected 7d window, caution badge, and data-as-of timestamp.
- Chart marker or marker-empty state, depending on selected issue.
- Issue summary card in success state if stored v2 content is available.
- Issue summary card in empty state as backup.
- Full information notice screen.
- Related-event candidate section for one curated issue.
- Static fallback banner or stale-data state if live/local API is unavailable.

Required local/live checks before Day 5 rehearsal:

- Start backend and frontend locally.
- Confirm Home -> Detail navigation works.
- Confirm `/api/issues` returns either live data or honest fallback data.
- Confirm `/api/issues/{id}/history?window=7d` returns chart points or honest
  insufficient-history state.
- Confirm `/api/issues/{id}/report` returns success for a chosen demo issue or
  the neutral empty state.
- Confirm the chosen demo issue has a related-event candidate, or prepare the
  candidate-unavailable narration.
- Check desktop and mobile widths for title, metric, chart, and report text
  overflow.

Day 5 rehearsal items:

- Pick one primary demo issue and one backup issue.
- Capture screenshots after local/live readiness check.
- Practice a 4-minute version and a 2-minute compressed version.
- Prepare one static screenshot sequence in case the local server cannot be
  shown during judging.
- Run `TASK-018` final wording pass across UI strings, report templates,
  event candidates, and this deck/demo copy.

## Judge Q&A Draft

| Question | Safe answer |
|---|---|
| Is this predicting what will happen? | No. It shows how expectations reflected in public Polymarket data have moved over time. The product is built as an issue-monitoring and interpretation-support dashboard. |
| Does this represent the public at large? | No. It reflects participant activity in a specific public data venue. Every major data screen includes that boundary with data-as-of timing and interpretation caution. |
| How do you avoid implying causes? | We do not auto-link news to movements. Related-event entries are manually curated candidates and are labeled as context, not causes. |
| Why use fixed-section summaries? | The summary is constrained to predefined sections so it can explain the issue, current data reading, conditional scenarios, checkpoints, and caution without open-ended analysis. |
| What happens when live data is unavailable? | The API can serve static fallback data with an honest data-as-of timestamp. The demo still shows the same flow without claiming fresh collection. |
| What did the team actually build in 5 days? | A React dashboard/detail flow, FastAPI read endpoints, normalized issue data, metric calculation, 5pp threshold markers, caution badges, stored report read path, v2 report schema, and manually curated context candidates. |
| Why is the MVP scope narrow? | The risk is not only build time; it is also framing. The MVP focuses on one clear user path and keeps accounts, saved lists, digest features, and automated event matching outside the hackathon build. |
| What comes next after the MVP? | Post-MVP work can improve content-ready exports, saved issue review, periodic briefings, broader categories, and stronger evaluation, but only after the safety frame remains intact. |

## Wording Check

Checked:

- This report's deck outline
- This report's demo script
- This report's fallback narration
- This report's judge Q&A draft
- `reports/task-040-demo-script-deck-draft-prompt.md`
- `memory/session.md`

Result:

- Basic hard-block English wording scan passed after replacing ambiguous
  update wording in the prompt file.
- The draft avoids future outcome assertions, automatic causality claims,
  participant-level browsing, and reader-action framing.
- The draft intentionally leaves comprehensive cross-surface copy review to
  `TASK-018`.

Lines requiring `TASK-018` attention:

- The final deck screenshots should be checked after image capture because slide
  titles, captions, and screenshot-visible UI strings can introduce new copy.
- Any chosen live issue title from Polymarket should be reviewed in context
  before presentation.

## Closeout Notes

`TASK-040` definition of done is met:

- Deck outline covers problem, current alternatives, product flow, safeguards,
  implementation realism, and next-step story.
- Demo script follows Home -> Detail -> Chart -> Summary -> caution notice ->
  manual context candidate.
- Fallback narration covers live/local data unavailability, report absence,
  insufficient chart history, and missing context candidates.
- Product framing stays as issue monitoring and interpretation support.
- Day 5 slide, screenshot, and rehearsal checklist is included.

Remaining Day 5 items:

- Convert the outline into final slides.
- Capture final screenshots from the chosen live/local path.
- Rehearse the primary and compressed demo versions.
- Run and record `TASK-018` final wording-safety pass.
