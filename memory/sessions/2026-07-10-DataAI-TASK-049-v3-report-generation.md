<!--
Purpose:        Archived TASK-049 Data/AI v3 generation session handoff
Owner:          Data/AI Implementer
Update Trigger: TASK-049 implementation follow-up
Harness Version: 1.1
-->

# Data/AI Session - TASK-049 v3 Report Generation

## Session Info

- **Date**: 2026-07-10
- **Role**: Data/AI Implementer
- **Branch**: `data-ai/TASK-049-v3-report-generation`
- **Status**: Implementation complete, tests green; status `review` pending
  Reviewer/PM close-out alongside `TASK-050`/`TASK-051`

## Outcome

`app/core/ai_report.py` and `app/core/ai_report_batch.py` now generate the
ADR-033 v3 eight-field report content instead of the v2 issue-explainer shape.
`PROMPT_VERSION` is `"v3"`.

Design (recorded as ADR-034): only three fields are LLM-authored prose -
`issue_overview`, `current_data_reading`, `possible_outlook` - constrained by
a tightened system prompt that never sees the related-event candidate at all.
The other five fields are built deterministically from `ReportPromptInputs`:

- `possible_drivers` - one of two fixed Korean literals (with/without a
  reviewed candidate), never the actual title/date text.
- `external_context` - verbatim pass-through of the curated `RelatedEvent.note`
  or `null`.
- `what_to_check` - a fixed checklist template with conditional clauses for
  end date / reviewed candidate presence.
- `data_limitations` - independently detects missing-history, low-activity,
  and high-volatility flags from raw snapshot/metric inputs (not the
  collapsed `confidence_level` enum alone) and always includes the
  representativeness disclaimer.
- `caution_note` - exact literal lookup by `confidence_level`, copied
  verbatim from `backend/API_CONTRACT.md`'s caution matrix.

`assemble_report_content()` merges the LLM's three fields with the five
deterministic ones into this module's own `ReportContent` (a structural copy
of the ADR-033 contract, intentionally kept out of `app/schemas/issues.py` so
Backend's `TASK-050` schema edits don't collide - see the parallelization plan
in `reports/day-5-v3-implementation-allocation.md`).

`run_safety_filter()` gained the ADR-033 Korean hard-block terms and Korean
causal/forecast regex patterns, with a carve-out (`예측(?!시장)`) so the
approved "예측시장" (prediction market) domain term used in every caution
literal is never mistakenly flagged by the new forecast-word ban - this was
the one real bug caught during test iteration (every deterministic
`caution_note` was initially self-rejecting). A new `run_semantic_checks()`
adds cross-field checks beyond phrase/pattern scanning: exact caution-literal
match, exact possible_drivers-literal match, and an
external-context candidate-not-cause qualifier check.

`app/core/ai_report_batch.py::build_prompt_inputs_for_market` now also
resolves the tracked `MarketOutcome.outcome_label`, `Market.end_date`,
snapshot `volume_24h`/`liquidity`, and the curated `RelatedEvent`'s
title/date/note as separate fields (previously combined into one string).
`generate_report_for_market` runs `parse_llm_fields` -> `assemble_report_content`
-> `run_safety_filter` -> `run_semantic_checks` before storing a `status=success`
row; any failure at any stage discards the output and keeps the previous
successful report live, matching the existing retry-once-then-fail behavior.

## Verification

- `pytest` (backend, in-memory SQLite + fake `LLMClient` only): 170 passed.
  The only failures in the full suite (`tests/test_issues_contract.py`, 5
  tests) are pre-existing and unrelated to this task - confirmed via
  `git stash` against the pre-TASK-049 tree, in Backend/`TASK-050`'s territory
  (live-mode DB-backed detail/history/report routes), not touched here.
- `ruff check` passes on all changed files.
- No live OpenAI/OpenRouter call was made; no write to any configured/shared
  database was performed or is needed for this task.

## Scope Boundary

Did not touch `app/schemas/issues.py`, `app/api/routes/issues.py`, or any
frontend file - those remain Backend's (`TASK-050`) and Frontend's
(`TASK-051`) scope. No database schema, dependency, infrastructure, or
deployment change was made.
