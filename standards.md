<!--
Purpose:        Code, documentation, and content-safety standards
Owner:          Reviewer
Update Trigger: Code style changes, new tooling, wording policy changes
Harness Version: 1.1
-->

# standards.md — Outlook Signals Standards

_Last updated: 2026-07-11_

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

**Korean v3 additions — hard block in UI, fallback strings, and AI/template output:**
`베팅, 매수, 매도, 포지션, 롱, 숏, 수익, 승률, 배당, 추천, 보장, 확정, 따라하기, 고수, 전문 트레이더, 고수익, 기회`

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
