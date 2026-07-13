# Technical Design: Security and Operating Risk

_Source: implemented security boundaries and accepted operating risks._

---

## 11. Security and Safety Considerations

| Concern                        | Implemented approach                                                                                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Financial and participant data | The system never handles funds, accounts, wallets, individual positions, or participant profiles                                                  |
| Secrets                        | Database and provider credentials are supplied through ignored environment files or deployment environment variables                              |
| Network exposure               | Caddy terminates TLS; only the Frontend gateway binds to the host; the Backend remains on isolated Docker networks                                |
| CORS                           | The API allows the deployed Frontend origin plus local development origins                                                                        |
| Input validation               | FastAPI and Pydantic validate public query, path, body, provider-output, and event payloads                                                       |
| AI output                      | Evidence, source, wording, numeric, leakage, Markdown, and schema validation run before storage and again where public reconstruction requires it |
| Logging                        | Full prompts, provider responses, bearer capabilities, and conversation content are never logged                                                  |
| Failure                        | Provider, validation, storage, and stream failures expose only safe error states and never replace a previous valid report                        |

### 11.1 Scenario-conversation boundary

- One anonymous session belongs to one issue and expires after 24 hours.
- A random 256-bit bearer capability authorizes every owned operation; only its
  hash is stored, and it never appears in a URL, log, provider prompt, or
  analytics event.
- The model has no tools or direct database access. Server code constructs a
  minimal typed bundle and treats external excerpts and user text as untrusted.
- Server-owned premise classes prevent user or model assumptions from becoming
  confirmed facts across turns.
- Raw HTML and model-authored active links or media are disabled. Complete blocks
  pass safety, leakage, premise, numeric, and restricted-Markdown validation
  before authenticated replay.
- Message, turn, context, concurrency, timeout, and USD limits fail before
  provider queueing where possible. Safety and parse failures do not retry
  automatically.
- Conversation content is deleted on expiry or owner request. Logs retain only
  content-free correlation, timing, usage, and safe failure metadata.
- Request ceilings and queued-request relaunch limits are process-local; a
  multi-instance deployment must not assume they are shared global limits.

## 15. Accepted Operating Risks

| Risk                               | Current handling                                                                                                                                |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Sparse market history              | Missing comparison windows remain unavailable and visibly limited                                                                               |
| Missing citation annotations       | Context publication fails safely to a zero-source state                                                                                         |
| Worker interruption                | Leases and bounded request-scoped recovery cover running and eligible scenario requests; briefing requests can be recovered by exact request ID |
| Provider latency or failure        | The UI uses validated-block SSE with polling and last-known-good fallback                                                                       |
| Small PostgreSQL connection budget | Each process defaults to a 3+1 connection pool                                                                                                  |
| Frontend chart bundle size         | The current production build retains a non-blocking size warning                                                                                |
| Action-runtime maintenance warning | The market-data workflow remains functional; future version changes require infrastructure review                                               |

## 17. Maintenance Rules

- Existing migrations are immutable; schema changes use a new append-only
  migration.
- Normal scheduled collection never invokes provider-backed generation.
- Production-data writes, deployment, schema, dependency, infrastructure,
  provider, and wording-policy changes follow `AGENTS.md`.
- Security, API, and safety behavior changes must update the corresponding
  executable tests and canonical documentation in the same change.
