# TASK-041 Report Generation Readiness Notes

_Date: 2026-07-09_
_Owner: Data/AI Implementer_
_Branch: `data-ai/TASK-041-report-generation-readiness`_

## Summary

`build_prompt_inputs_for_market()` now builds prompt inputs from the latest
`market_snapshots` row whose `captured_at` timestamp is less than or equal to
the selected `market_metrics.computed_at` timestamp. This matches the
historical seed path, which records seeded metric rows one microsecond after
the latest source snapshot.

The lookup still returns no prompt inputs when there is no snapshot at or
before the metric timestamp. Future-only snapshots are not used, and no metric
or value is fabricated.

## Before Approval

The no-report empty state is normal until an explicitly approved database-write
generation run has happened. In that state:

- `/api/issues/{id}/report` may return `{"status":"not_yet_generated"}`.
- The frontend summary card should show its neutral not-yet-generated state.
- `ai_reports=0` is expected if no approved database write has run.

Do not treat this state as a frontend or API failure before the approved
database-write generation step.

## Approved-Only Procedure For A Saved Summary

Only proceed after explicit human approval for writing report rows to the
configured local/dev database. Per the 2026-07-09 user clarification recorded
in ADR-022, the provided `OPENAI_API_KEY` may be used for project-scoped OpenAI
report generation without separate per-run approval.

1. Confirm the checked-out code includes `TASK-041`.
2. Confirm the environment target without printing secret values:
   - `ENV` is `local`, `dev`, `development`, or another approved non-production
     target.
   - `DATABASE_URL` points to the approved local/dev database.
   - `OPENAI_API_KEY` and `OPENAI_MODEL` are configured.
3. Confirm snapshot and metric rows already exist. The batch entry point selects
   the latest run with `max(market_metrics.computed_at)`.
4. Run the approved database-write generation command:

   ```bash
   cd backend
   python -m app.core.ai_report_batch
   ```

5. Verify with read-only checks:
   - `GET /api/issues/{id}/report` returns `status: "success"` for an issue
     with a newly stored successful row.
   - A read-only database count can confirm `ai_reports` rows with
     `status='success'`.

No real LLM call or shared/dev database write was performed while preparing
these readiness changes.
