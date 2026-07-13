<!--
Purpose:        Current external dependencies and runtime constraints
Owner:          Backend / Frontend maintainers
Update Trigger: Dependency or supported-runtime change
Harness Version: 1.1
-->

# Dependencies — Outlook AI Signals

_Last updated: 2026-07-13_

Package manifests and lockfiles are the executable source of truth. This file
summarizes the supported runtime and major integration choices.

## Frontend

| Package           | Version          | Purpose                                 |
| ----------------- | ---------------- | --------------------------------------- |
| React / React DOM | ^18.3.1          | Component runtime                       |
| React Router DOM  | ^7.18.0          | Browser routing                         |
| Recharts          | ^2.12.7          | Time-series charts                      |
| Vite              | ^5.4.6           | Development server and production build |
| TypeScript        | ^5.5.4           | Static typing                           |
| Tailwind CSS      | ^3.4.10          | Styling                                 |
| ESLint / Prettier | package manifest | Linting and formatting                  |

## Backend

| Package           | Version              | Purpose                                                 |
| ----------------- | -------------------- | ------------------------------------------------------- |
| FastAPI           | 0.115.0              | Public API                                              |
| Uvicorn           | 0.30.6               | ASGI server                                             |
| Pydantic          | 2.9.2                | Request, response, and provider-output validation       |
| SQLAlchemy        | 2.0.35               | PostgreSQL persistence                                  |
| psycopg           | 3.2.3                | Primary PostgreSQL driver                               |
| psycopg2-binary   | 2.9.10               | Compatibility PostgreSQL driver                         |
| python-dotenv     | 1.0.1                | Local environment loading                               |
| OpenAI Python SDK | 2.44.0               | OpenAI-compatible provider client, including OpenRouter |
| httpx             | 0.27.2               | Development/test HTTP client                            |
| Ruff / pytest     | requirements-dev.txt | Linting and tests                                       |

The supported local Backend runtime is Python 3.11.

## External systems

| System                                  | Use                                                                             |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| Polymarket Gamma API                    | Public market and event metadata                                                |
| Polymarket CLOB API                     | Historical price data                                                           |
| PostgreSQL                              | Application, evidence, report, and ephemeral scenario storage                   |
| OpenAI-compatible provider / OpenRouter | Bounded context research, briefing generation, and tool-free scenario responses |
| GitHub Actions                          | Four-hour market-data-only collection                                           |
| Docker Compose                          | Backend and Frontend process orchestration                                      |
| Caddy                                   | TLS termination and public reverse proxy                                        |

## Dependency policy

- Adding a dependency or changing a major version requires human approval.
- Minor and patch updates require review and full relevant checks.
- Dependency changes must update the manifest, lockfile, this summary, and the
  applicable deployment image.
- No authentication, account, message-queue, task-runner, or financial-charting
  dependency may be added without an explicitly approved product and
  architecture change.
