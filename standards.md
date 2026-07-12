<!--
Purpose:        Code, documentation, and content-safety standards
Owner:          Reviewer
Update Trigger: Code style changes, new tooling, wording policy changes
Harness Version: 1.1
-->

# standards.md — Outlook Signals Standards

_Last updated: 2026-07-12_

## Code Style

### Frontend (TypeScript)
- **Indentation**: 2 spaces
- **Max line length**: 100
- **Naming**: variables/functions `camelCase`, components/types `PascalCase`, constants `UPPER_SNAKE_CASE`
- **Charts**: Recharts only, line charts only — no candlestick rendering (UX Design §3.4)
- **Color**: no green/red "gain/loss" finance-style coloring; prefer neutral accent + arrow/icon direction (UX Design §6)

### Backend (Python)
- **Indentation**: 4 spaces
- **Max line length**: 100 (ruff/black default)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- **Models**: Pydantic for all API request/response shapes and normalized data objects

## Commit Messages

```
<type>(<scope>): <subject>
```
Types: `feat` | `fix` | `docs` | `style` | `refactor` | `test` | `chore` | `security`

## PR Rules

- Title follows commit message format
- Reviewer sign-off required before merge (rotates among the 4 team members)
- Self-merge is not allowed
- Any PR touching user-facing copy or AI templates must pass the Content Safety Lint below

## Test Standards

- Given the 5-day timeline: prioritize tests for change-calculation logic, inflection-point threshold logic, and the AI-output banned-phrase filter (highest-risk, highest-value-per-minute per Technical Design's time-pressure framing)
- Manual QA pass on the full demo flow (Home → Detail → Chart → Summary) before Day 5 — no formal coverage target for a hackathon MVP

## Security Standards

- No hardcoded secrets in code — Polymarket/LLM/DB credentials via environment variables only (Technical Design §11)
- Validate all API query params via FastAPI/Pydantic (enum checks on `window`/`sort`, type checks on ids)
- CORS restricted to the deployed frontend origin + localhost for dev
- Never log full LLM prompts/responses (standing rule even though there's no user PII in MVP)

## Content Safety Lint (project-specific — treat as a blocking check, not a style guideline)

Every user-facing string and every AI/template output must be checked against these lists before it ships. See `memory/glossary.md` for the full term list and UX Design §5 for the source policy.

**Prohibited — hard block on any occurrence:**
`bet, buy, sell, trade, position, long, short, profit, win rate, odds, copy trader, follow this user, expert trader, best pick, recommended outcome, high-return opportunity, guaranteed, guaranteed prediction, signal to act, recommend, recommendation`

**Korean hard blocks — any active-v8 occurrence fails:**
`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 따라하기, 고수, 전문 트레이더, 고수익`

**Active-v8 contextual expressions — fail closed unless one approved context matches:**

| Expression | Allowed without source evidence | Allowed with source evidence |
|---|---|---|
| `확정` | Explicit negation/limitation or `확정 여부` verification inquiry | Attributed sentence plus referenced source support containing `확정`/`confirmed` |
| `보장` | Explicit negation/limitation such as `보장하지 않는다` | Attributed sentence plus referenced source support containing `보장`/`guarantee` |
| `추천` | Explicit rejection such as `추천하지 않는다` | Institutional attribution plus referenced source support containing `추천`/`권고`/`recommend` |
| `기회` | Explicit rejection such as `기회로 제시하지 않는다` | Procedural attribution plus referenced source support containing `기회`/`opportunity` |
| `전망` | Explicit negation/limitation or `전망 여부` inquiry | Attributed sentence plus referenced source support containing `전망`/`outlook`/`forecast` |
| `원인` | Existing candidate-not-cause/explicit-negation forms | Attributed sentence plus referenced source support containing `원인`/`cause` |

Source-backed allowance requires both conditions in the same v8 section: an
exact `source:*` evidence reference and visible attribution such as `공식 문서`,
`기관`, `정부`, `위원회`, `보고서`, `발표`, `공지`, `밝혔다`, or `따르면`. A source
reference alone never permits the expression. Headline and summary have no
section evidence scope, so only the no-source negation/inquiry forms may pass.
Ambiguous, predictive, outcome-asserting, or unsupported uses remain blocking.
V1-v7 keep their historical flat filters for reconstructibility.

**Use-carefully — only with a qualifying phrase attached, never standalone:**
`signal, alert, watch, momentum, confidence, market activity, probability spike` — see UX Design §5.2 for the exact safe phrasing pattern for each.

**Structural rules:**
- V1-v6 AI output keeps the historical causal-verb restrictions. V7 may quote
  or summarize a causal interpretation only when it is explicitly attributed
  to an accepted source and its exact supported claim; the product must never
  infer that context explains an observed movement.
- V1-v6 related-event candidates keep the historical "candidate, not cause"
  qualifier. V7 source material instead exposes A-C source level, attribution,
  and supported claims; timing overlap alone still cannot be presented as a
  relationship.
- No numeric confidence stated as a probability of a real-world outcome (e.g., never "73% likely to happen")
- Every metric-bearing surface must ship with its caution badge in the same viewport — no exceptions for "obviously fine" markets
- v3 AI reports must validate against ADR-033's exact eight-field contract before storage; missing, extra, or unsafe fields block storage
- v4 reports must validate against ADR-038's exact seven-field contract and
  evidence references before storage. Metric statements require stored metric
  IDs; context statements require verified candidate IDs with stored citation
  sources. Missing or inconsistent evidence blocks storage and public serving.
- Automated context accepts only OpenRouter API `url_citation` annotations.
  Model-body URLs, unsupported dates/entities, hard-gate failures, verifier
  disagreements, conflicts, and non-verified candidates must fail closed.
- OpenRouter usage for TASK-056~065 must remain within the cumulative USD 100
  approval and be recorded without prompts, responses, keys, or secrets.
- v3 related-event and v4 verified-context candidates must carry the
  candidate-not-cause boundary; timing or co-occurrence never establishes a
  relationship with the observed movement.
- v7 writer output must validate against ADR-051's flexible stable envelope.
  Unknown refs, unsupported source claims, unsafe links, invented evidence,
  unattributed level-C claims, or irreconstructible output block publication;
  ordinary style, ordering, English-term, and moderate-overlap findings are
  diagnostics rather than automatic rejection.
- v8 keeps the v7 evidence/source publication blockers while requiring the
  TASK-112 issue-centered envelope. `current_situation` and `recent_change`
  are mandatory, section types are unique, limitations may appear once, and
  the public UI must not repeat the deterministic limitations block when the
  authored limitations section is present.
- TASK-113 may widen v8 discovery to a deterministic 90-day or 180-day horizon
  and common entity/issue aliases. Publication still requires an exact safe
  annotation URL, publisher title/domain, non-empty excerpt, issue relevance,
  narrow supported claim, source-parent linkage, A-C attribution, and all
  conflict, conditional-verifier, wording, and no-causal-inference gates.
- TASK-116 applies contextual wording only to active v8. It must run identically
  before storage and during read-time reconstruction. Positive contextual terms
  require same-section source support and attribution; explicit negation or
  verification-inquiry forms remain source-free. Ambiguous uses fail closed.
- TASK-124 locks the approved next-contract distinction between a freer current
  summary and a free-form scenario conversation. Active v8 remains unchanged
  until TASK-131 acceptance. The summary may treat ordinary explanatory prose,
  ordering, section count, and zero-source coverage as diagnostics, but exact
  observations and current external facts remain blocking and reconstructible.
- Scenario conversation has no required visible section template. Every premise
  remains server-classified as confirmed fact, stored observation, user
  assumption, model scenario, or unverified context. An assumption cannot be
  promoted by the model. Permanent financial/action, real-world-result,
  unsupported-relationship, privacy, individual-participant, secret-leakage,
  and unsafe-rendering rules remain blocking in every conversational context.
- Policy/lint docs and tests may quote prohibited expressions only to define or verify the blocking rule; demo-visible docs and product copy may not normalize those terms as user-facing language

## Documentation Standards

- Comments required on all public functions and API endpoints
- Inline explanation for non-obvious logic (e.g., why a threshold constant has its current value)
- Record key decisions in `memory/decisions.md`

## Review Checklist (before requesting review)

- [ ] Code style compliant
- [ ] No security issues
- [ ] Content Safety Lint passed (if any copy/template touched)
- [ ] Data-as-of timestamp + caution badge present (if a new data screen/component was added)
- [ ] No AGENTS.md restrictions violated
