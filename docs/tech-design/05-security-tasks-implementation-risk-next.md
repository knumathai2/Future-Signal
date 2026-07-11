# Technical Design: Security, Tasks, Implementation Order, Risk, Next Steps

_Source: former project-root Technical Design sections 11-17._

---

## 11. Security and Safety Considerations

| Concern | Approach |
|---|---|
| No financial transactions ever processed | The system never touches funds, wallets, or user positions — this is a structural property, not just a policy, and it's the main reason this architecture carries far less regulatory/security surface than a real trading system |
| No PII in MVP | No accounts, no personal data collected at all in the hackathon build; Phase 2 watchlist should collect the absolute minimum (email or anonymous device id only) |
| Secrets management | LLM API key and DB credentials in platform environment variables, never committed to the repo |
| CORS | Restrict the API to the deployed frontend origin (plus localhost for dev) |
| Input validation | All query params validated by FastAPI/Pydantic (enum checks on `window`/`sort`, type checks on ids) before hitting the DB |
| AI output safety | Enforced at generation time (Section 10.4), not just at display time — never trust the model to self-censor without a mechanical check |
| Rate limiting on public endpoints | A basic per-IP rate limit (e.g., via a FastAPI middleware) is a reasonable should-have to prevent accidental scraping load during the demo period, though not critical for a 5-day hackathon audience |
| Logging hygiene | Never log full LLM prompts/responses containing user data (moot for MVP since there's no user data, but worth stating as a standing rule before Phase 2 personalization exists) |

---

## 12. MVP Development Task Breakdown

Organized by function; owner maps to the 4-person team from PRD §13 (PM, Frontend, Backend/API/DB, Data/AI) — one person may own multiple functional rows below.

### Must-Have

| Task | Description | Owner | Difficulty | Dependency | Output |
|---|---|---|---|---|---|
| DB schema creation | Create tables from Section 4 (MVP set) | Backend | Low | none | Migration script |
| API contract draft | Define request/response shapes for Section 5 endpoints | Backend + PM | Low | DB schema | OpenAPI doc (free from FastAPI) |
| Batch collector: fetch + normalize | Steps 1–2 of Section 6 | Data/AI | Medium | curated market id list | Script producing normalized objects |
| Batch collector: snapshot + metrics | Steps 3–5 of Section 6 | Data/AI + Backend | Medium | schema, fetch script | Populated `market_snapshots`/`market_metrics` |
| Signal detection | Step 6 of Section 6 | Data/AI | Low | metrics populated | Populated `issue_signals` |
| `/api/issues`, `/api/issues/:id`, `/api/issues/:id/history` | Core read endpoints | Backend | Medium | DB populated | Working API |
| `/api/health` | Trivial health check | Backend | Low | none | Working endpoint |
| Home dashboard UI | Ranked issue cards | Frontend | Medium | `/api/issues` | Working screen |
| Issue detail UI + chart | Detail page with Recharts line chart | Frontend | Medium | `/api/issues/:id`, `/history` | Working screen |
| Caution badge component | Reusable badge per UX Design | Frontend | Low | metrics/confidence field | Component |
| AI report generation function | Section 9–10 implementation | Data/AI | Medium–High | metrics + prompt design | `ai_reports` rows |
| AI report display UI | Render stored report | Frontend | Low | `/api/issues/:id/report` | Working screen |
| Disclaimer copy + footer + dedicated screen | UX Design §8 copy wired in | Frontend + PM | Low | copy finalized | Live on every screen |
| Copy/wording lint pass | Check all UI strings against UX Design §5 | PM | Low | UI mostly built | Sign-off checklist |
| 3–5 curated related events | Manual data entry into `related_events` | PM/Data | Low | demo issue selection | Populated table |
| Deployment (all three services) | Vercel + Railway/Render + Supabase | Backend | Medium | working app | Live URL |
| Demo script + fallback data | Static JSON fallback if live pipeline breaks during demo | PM | Low | working app | Backup plan |

### Should-Have

| Task | Description | Owner | Difficulty | Dependency | Output |
|---|---|---|---|---|---|
| Category filter | Frontend + `/api/categories` | Frontend + Backend | Low | markets have categories | Filter UI |
| `/api/signals` feed endpoint + UI | Cross-market "recent changes" view | Backend + Frontend | Medium | signals populated | Working screen |
| Volatility/attention metrics | P1 metrics from Service Design §5 | Data/AI | Medium | more history accumulated | Extra `market_metrics` columns populated |
| Empty/loading/error states polish | UX Design §6 empty-state copy | Frontend | Low | core screens done | Polished states |
| Sentry integration | Error capture | Backend | Low | deployed app | Error dashboard |
| Report regeneration admin trigger | Manual re-run for demo issues before presenting | Data/AI | Low | report generation working | Script/endpoint |

### Nice-to-Have

| Task | Description | Owner | Difficulty | Dependency | Output |
|---|---|---|---|---|---|
| Search endpoint + UI | Simple title search | Backend + Frontend | Low | issue list working | Search box |
| Responsive/mobile polish | Layout refinement | Frontend | Low | core UI done | Polished mobile view |
| Basic rate limiting middleware | Section 11 | Backend | Low | API stable | Middleware |
| README / setup docs | For judges or future contributors | PM | Low | app complete | Doc |

---

## 13. Must-Have / Should-Have / Nice-to-Have Scope

This mirrors PRD §6.3–6.5 exactly at the product level; Section 12 above is the technical task-level breakdown of that same scope split. No new scope is introduced here beyond what PRD already committed to — this document exists to make that scope buildable, not to expand it.

---

## 14. Implementation Order

Recommended build sequence (compatible with PRD's 5-day plan, §14):

1. **DB schema + API contract** (Day 1) — must exist before frontend or data work can proceed in parallel.
2. **Frontend starts against mock JSON matching the API contract, in parallel with** batch collector build (Day 1–2) — this is the single most important parallelization to protect the timeline, per PRD's stated role-operating-principle.
3. **Batch collector: fetch → normalize → snapshot** (Day 1–2) — get real data flowing before building anything downstream of it.
4. **Metrics + signal detection** (Day 2–3) — depends on having several snapshot cycles of real data to compute deltas against.
5. **Core API endpoints wired to real data** (Day 2–3) — replaces the frontend's mock JSON.
6. **AI report generation** (Day 3–4) — depends on metrics existing; this is correctly the *last* data-dependent piece to build, since it depends on everything upstream being stable.
7. **UI polish, disclaimer wiring, copy lint pass** (Day 4).
8. **Deployment, demo rehearsal, fallback data prep** (Day 5).

---

## 15. Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Polymarket API field structure differs from assumptions in Section 4/6 | Medium | High | Validate against a live pull on Day 1 before finalizing the schema (also flagged in Service Design §13) |
| AI report generation costs or latency run higher than expected | Low–Medium | Medium | Cost controls in Section 9 (cap per run, regenerate only on change) designed in from the start, not retrofitted |
| Metric thresholds (5pp signal, confidence cutoffs) produce noisy or empty results on real data | Medium | Medium | Treat all thresholds as constants to tune on Day 2 once real data is visible, not as fixed requirements |
| Batch job fails silently during the demo window | Medium | High | `data_collection_logs` + fallback static JSON dataset (Section 12, "demo script + fallback data") as a rehearsed backup |
| Team loses time to stack/tooling setup instead of building | Medium | High | Every stack choice in Section 2 was picked specifically for zero-config hosted setup — resist the urge to substitute a "better" but less familiar tool mid-hackathon |
| Schema or API accidentally grows a wallet/participant-level field "just in case" | Low | High (product-policy risk, not just technical) | Section 4.12's explicit exclusion list should be treated as a standing constraint on schema PRs, same as Service Design §8's feature gate |

---

## 16. Open Questions

1. Exact Polymarket endpoint(s) and auth/rate-limit behavior for the curated market list — needs a Day 1 spike before the schema is fully locked (shared with Service Design §12, Q4).
2. Final `heat_score` weighting — start with a simple formula (Section 7) and expect to eyeball-tune it once real data is visible; not worth over-designing before that.
3. Whether `/api/issues/:id/metrics` ships as a separate endpoint or folds into the detail response — recommend folding for MVP and only splitting out if the detail payload gets unwieldy.
4. Collection frequency (hourly vs. every 4 hours) — depends on how much real movement is visible in the curated market set once Day 1 data validation happens.
5. Whether Sentry (should-have) is worth the setup time given the team size — low cost either way, defer the decision to whoever finishes their must-have tasks first.

---

## 17. Next Steps for Development

1. Run a Day 1 spike against the live Polymarket Gamma/CLOB APIs to confirm field names and rate limits before finalizing the `markets`/`market_outcomes` schema in Section 4.
2. Stand up the three hosted services (Supabase/Neon, Railway/Render, Vercel) and confirm a "hello world" deploy on all three before writing feature code — removes deployment as a Day 5 surprise.
3. Write the DB migration and share the generated FastAPI OpenAPI doc with the Frontend role immediately, so mock-JSON frontend work matches the real contract from the start.
4. Implement Section 6 steps 1–4 (fetch through snapshot storage) first and get one full successful batch run before writing any metric/signal/AI code — everything downstream depends on this working.
5. Once this document, PRD, Service Design, and UX Design are all in hand, they're sufficient to write actual sprint tickets directly from Section 12's task tables — no further planning document should be needed before implementation starts.

### 17.1 Approved post-MVP execution

ADR-038 activates TASK-056~065 as the only approved automated-context program.
The binding sequence, file ownership, tests, handoffs, and stop conditions are
in `reports/task-055-automated-context-execution-plan.md`. No successor starts
before its dependency passes. Deployment, production-database writes, new
dependencies, and infrastructure changes are not authorized by this program.
