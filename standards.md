<!--
Purpose:        Code, documentation, and content-safety standards
Owner:          Reviewer
Update Trigger: Code style changes, new tooling, wording policy changes
Harness Version: 1.1
-->

# standards.md — Outlook AI Signals Standards

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

- Backend changes must pass Ruff and the relevant pytest suite.
- Frontend changes must pass typecheck, lint, parser regressions, and the
  production build.
- Copy, evidence, generation, and rendering changes require their focused safety
  regressions plus manual verification of timing and caution states.

## Security Standards

- No hardcoded secrets in code — Polymarket/LLM/DB credentials via environment variables only (Technical Design §11)
- Validate all API query params via FastAPI/Pydantic (enum checks on `window`/`sort`, type checks on ids)
- CORS restricted to the deployed frontend origin + localhost for dev
- Never log full provider prompts/responses, bearer capabilities, or scenario
  conversation content

## Content Safety Lint (project-specific — treat as a blocking check, not a style guideline)

Every user-facing string and every AI/template output must be checked against these lists before it ships. See `memory/glossary.md` for the full term list and UX Design §5 for the source policy.

**Prohibited — hard block on any occurrence:**
`bet, buy, sell, trade, position, long, short, profit, win rate, odds, copy trader, follow this user, expert trader, best pick, recommended outcome, high-return opportunity, guaranteed, guaranteed prediction, signal to act, recommend, recommendation`

**Korean hard blocks — any active-v8 occurrence fails:**
`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 따라하기, 고수, 전문 트레이더, 고수익`

**Active-v8 contextual expressions — fail closed unless one approved context matches:**

| Expression | Allowed without source evidence                                  | Allowed with source evidence                                                                  |
| ---------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `확정`     | Explicit negation/limitation or `확정 여부` verification inquiry | Attributed sentence plus referenced source support containing `확정`/`confirmed`              |
| `보장`     | Explicit negation/limitation such as `보장하지 않는다`           | Attributed sentence plus referenced source support containing `보장`/`guarantee`              |
| `추천`     | Explicit rejection such as `추천하지 않는다`                     | Institutional attribution plus referenced source support containing `추천`/`권고`/`recommend` |
| `기회`     | Explicit rejection such as `기회로 제시하지 않는다`              | Procedural attribution plus referenced source support containing `기회`/`opportunity`         |
| `전망`     | Explicit negation/limitation or `전망 여부` inquiry              | Attributed sentence plus referenced source support containing `전망`/`outlook`/`forecast`     |
| `원인`     | Existing candidate-not-cause/explicit-negation forms             | Attributed sentence plus referenced source support containing `원인`/`cause`                  |

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

- No numeric confidence may be stated as the probability of a real-world outcome.
- Every metric-bearing surface must include its caution text in the same
  viewport.
- Automated context accepts only provider-returned citation annotations.
  Model-body URLs, unsupported dates/entities, hard-gate failures, verifier
  disagreement, conflicts, and rejected candidates fail closed.
- V8 output requires reconstructible evidence references, safe source-parent
  links, supported claims, current timing, deterministic caution, and the
  issue-centered section envelope. `current_situation` and `recent_change`
  are mandatory; section types are unique and limitations appear at most once.
- Contextual wording validation runs identically before storage and during
  read-time reconstruction. Positive contextual expressions require
  same-section source support and visible attribution; explicit negation or
  verification inquiry may be source-free. Ambiguous uses fail closed.
- Scenario conversations keep server-owned premise classes. An assumption cannot
  become a confirmed fact, and provider output cannot introduce unknown evidence
  references, unsupported numbers, unsafe links, executable Markdown, secrets,
  or individual-participant content.
- Policy/lint documents and tests may quote prohibited expressions only to define
  or verify the blocking rule; product and presentation copy may not normalize
  them as user-facing language.

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
