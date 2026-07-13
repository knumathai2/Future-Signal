# Technical Architecture Design: Outlook AI Signals

_Status: implemented final architecture, 2026-07-13._

Companion documents: [PRD](../prd/README.md),
[Service Design](../service-design/README.md), and
[UX Design](../ux-design/README.md).

---

## 1. Technical Design Summary

The system is a read-heavy issue-monitoring application with two bounded public
write paths: immutable briefing-generation requests and capability-owned
scenario sessions. The API records request state but never calls a provider
directly.

```text
Polymarket APIs
      |
      v
scheduled collector -> PostgreSQL <- FastAPI <- React/Vite
                            ^           |
                            |           +-- briefing request
                            |           +-- scenario request
                            |
                      isolated workers
                evidence -> validation -> stored blocks
```

Normal collection and provider-backed generation are separate. Stored,
individually validated blocks are replayed over SSE with polling and
last-known-good fallbacks.

## 2. Technology Stack

| Layer       | Implemented choice                                                 | Role                                                                       |
| ----------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| Frontend    | React 18, Vite, TypeScript, Tailwind CSS, Recharts                 | Responsive issue, chart, briefing, and scenario UI                         |
| Backend     | Python 3.11, FastAPI, Pydantic                                     | Public API and strict request/response validation                          |
| Persistence | PostgreSQL, SQLAlchemy, psycopg                                    | Append-only market, evidence, report, request, and ephemeral session state |
| Collection  | Python scheduled batch + GitHub Actions                            | Four-hour public market-data collection                                    |
| Generation  | OpenAI-compatible Python SDK with isolated workers                 | Bounded context research, v8 briefing, and tool-free scenario responses    |
| Streaming   | Server-sent events                                                 | Replay of complete validated briefing and scenario blocks                  |
| Deployment  | Docker Compose, Caddy, VPS                                         | Isolated Backend/Frontend networks and TLS termination                     |
| Testing     | pytest, Ruff, TypeScript, ESLint, parser scripts, production build | Contract, safety, and integration verification                             |

No account, authentication platform, message queue, wallet integration, or
financial charting library is included.

## 3. System Architecture

### 3.1 Collection path

The scheduled workflow fetches public Gamma records, normalizes active binary
issues, writes snapshots, calculates metrics and signals, and records collection
status. It receives no provider credentials and skips context and briefing
generation.

### 3.2 Read path

FastAPI serves issue, category, history, briefing, request-status, and validated
SSE data from PostgreSQL. When configured data is unavailable, issue reads use
timestamped fallback data and report/source reads return honest empty states.

### 3.3 Briefing path

A public POST appends or joins an immutable fingerprinted request. An isolated
worker optionally refreshes context, validates provider-returned citations,
generates strict NDJSON, persists each complete valid block, and commits the
final v8 report only after full-envelope validation.

### 3.4 Scenario path

A random bearer capability owns one 24-hour issue-scoped session. Each accepted
turn appends an immutable request. A tool-free worker receives only a typed
issue/evidence/premise bundle and bounded conversation history. Complete
paragraph/list blocks are stored only after premise, evidence, wording, numeric,
leakage, Markdown, and schema validation.

### 3.5 Deployment path

The checked-in production Compose profile runs the Backend and Frontend on
isolated Docker networks. The Frontend gateway alone binds to
`127.0.0.1:8600`; Caddy terminates TLS for the configured public host. The
Backend uses a separate outbound network for PostgreSQL and provider access.

### 3.6 Architectural invariants

- The API process does not call Polymarket or an AI provider.
- Scheduled collection does not run provider-backed generation.
- Missing data and evidence are never fabricated.
- Raw provider fragments never cross the public boundary.
- Previous valid reports remain available when a new request fails.
- Every public data surface retains timing and interpretation caution.
- Schema, dependency, infrastructure, deployment, production-data, provider,
  and wording-policy changes follow `AGENTS.md`.
