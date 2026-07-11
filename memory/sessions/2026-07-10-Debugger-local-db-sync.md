<!--
Purpose:        Archived handoff for the local DB sync and runtime diagnosis notes that followed ISS-010
Owner:          Debugger / Data-AI Implementer
Update Trigger: Session close
Harness Version: 1.1
-->

# Session Archive — Local DB Sync and Runtime Diagnosis

## Session Info

- **Date**: 2026-07-10
- **Agent Role**: Debugger / Data-AI Implementer
- **Branch**: `debug/ISS-010-actions-secrets`

## Local Runtime

- Started Docker Desktop and the existing local PostgreSQL 16 container.
- Applied the existing initial migration to the local-only `future_signal`
  database; all eight MVP tables were present.
- Started FastAPI on `http://127.0.0.1:8000` and Vite on
  `http://127.0.0.1:5173`; health, issue, frontend, and proxy reads returned
  HTTP 200.
- The initial empty local database correctly used static fallback data.

## Fallback Diagnosis

- Reproduced fallback dashboard titles that exposed raw category labels.
- Confirmed the local DB had no snapshot rows at the time, so the Backend
  intentionally returned two static sample issues.
- Confirmed those sample titles were absent from the Frontend title mapping;
  the generic title formatter therefore produced the observed labels.
- Classified this as the runtime form of existing TD-009; no code changed.

## Local DB Sync

- Verified the source was the remote development DB used by the successful
  scheduled batch and the destination was the local PostgreSQL container.
- Confirmed all eight application tables had matching columns before copying.
- Replaced local application-table contents in one transaction from the remote
  read-only snapshot: 67 markets, 67 outcomes, 33,438 snapshots, 350 metrics,
  2 issue-change markers, 115 reports, 0 related events, and 15 collection
  logs.
- Verified the latest copied successful batch processed 50 markets with 0
  failures and finished at `2026-07-10T06:16:01Z`.
- Verified `/api/issues` then served the live DB timestamp, the local browser
  rendered mapped Korean issue titles, and a top issue's report endpoint served
  stored v3 content.

No remote write, external provider call, source-code change, dependency change,
deployment, or wording-policy change was made.
