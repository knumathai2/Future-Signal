<!--
Purpose:        Code, documentation, and content-safety standards
Owner:          Reviewer
Update Trigger: Code style changes, new tooling, wording policy changes
Harness Version: 1.1
-->

# standards.md — Outlook Signals Standards

_Last updated: 2026-07-10_

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
`bet, buy, sell, trade, position, long, short, profit, win rate, copy trader, follow this user, expert trader, best pick, recommended outcome, high-return opportunity, guaranteed prediction, odds, signal to act`

**Korean v3 additions — hard block in UI, fallback strings, and AI/template output:**
`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 추천, 보장, 확정, 따라하기, 고수, 전문 트레이더, 고수익, 기회`

**Use-carefully — only with a qualifying phrase attached, never standalone:**
`signal, alert, watch, momentum, confidence, market activity, probability spike` — see UX Design §5.2 for the exact safe phrasing pattern for each.

**Structural rules:**
- No causal verbs in AI output (`because`, `due to`, `caused by`) — use `coincides with`, `occurred alongside` instead
- Related-event candidates must always carry the "candidate, not cause" qualifier
- No numeric confidence stated as a probability of a real-world outcome (e.g., never "73% likely to happen")
- Every metric-bearing surface must ship with its caution badge in the same viewport — no exceptions for "obviously fine" markets
- v3 AI reports must validate against ADR-032's exact field list before storage; missing, extra, or unsafe fields block storage
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
