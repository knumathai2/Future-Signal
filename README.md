# Outlook Signals

Outlook Signals is an issue-monitoring dashboard built from public aggregate
Polymarket data. It shows how reflected expectation values changed over time,
with data timestamps and interpretation cautions. It does not assert future
results or explain a movement without accepted source support.

## Repository

- `frontend/`: React 18, Vite, TypeScript, Tailwind CSS, and Recharts
- `backend/`: FastAPI, PostgreSQL reads, market-data collection, and the
  evidence-bounded v8 briefing worker
- `docs/`: product, service, technical, UX, archive, and retention guidance
- `memory/`: current project state, decisions, architecture, issues, and terms
- `tasks/` and `reports/`: durable task index and retained implementation evidence

## Local development

Backend, using Python 3.11:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` requests to the Backend at
`http://127.0.0.1:8000`. When no configured database is available, documented
static fallback states remain visibly timestamped.

## Verification

```bash
(cd backend && ./.venv/bin/ruff check . && ./.venv/bin/pytest)
(cd frontend && npm run typecheck && npm run lint && npm run test:report-parser && npm run build)
```

## Canonical guidance

- [Project constitution](AGENTS.md)
- [Product requirements](docs/prd/README.md)
- [Service design](docs/service-design/README.md)
- [Technical design](docs/tech-design/README.md)
- [UX design](docs/ux-design/README.md)
- [Current project state](memory/project.md)
- [Document retention](docs/document-retention-manifest.md)

Database schema changes, external dependencies, infrastructure changes,
deployments, production writes, and wording-policy changes require the
approvals defined in `AGENTS.md`.
