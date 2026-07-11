# TASK-094 / ISS-014 — Context Pipeline Observability

Date: 2026-07-11  
Owner: Data/AI Implementer + Debugger  
Branch: `debug/ISS-014-context-pipeline-observability`  
Status: complete

## Reproduction and root cause

When context research was requested without a configured independent verifier,
the CLI caught the builder exception, emitted an informational skip, and ran the
batch with both clients unset. The final log could therefore report success with
`context_success=0` and `context_failed=0`, even though the requested stage did
not run.

## Fix

- Added `context_requested` and a secret-free `context_reason_code` to the batch
  result and collection-log audit.
- Added isolated client-pair construction with safe reason codes:
  `context_research_client_unavailable`, `context_verifier_unavailable`, and
  `context_client_pair_incomplete`.
- A requested stage with incomplete clients now records
  `context_configuration_failed:<reason>` and the scheduled log is failed.
- Only explicit `--skip-context-research` (or the already separate stored-context
  writer mode) retains normal skip behavior.
- No key, exception message, prompt, or response is included in the reason code
  or audit log.
- The candidate list remains empty when configuration is incomplete, preserving
  fail-closed publication behavior.

## Verification

- Missing verifier at the direct batch boundary produces a failed log with the
  safe reason code despite zero context outcomes.
- Explicit skip remains a normal successful run.
- Client builder strips sensitive exception detail.
- CLI regression proves missing verifier returns exit code one and records
  `context_verifier_unavailable`.
- Context/scheduled focused suite: 103 passed.
- Full Backend suite: 373 passed.
- Ruff and diff checks: passed.

No workflow/runtime configuration, provider call, non-test database write,
dependency, migration, infrastructure, deployment, or production action
occurred. Adding a verifier setting to GitHub Actions or another runtime remains
a separately approval-gated infrastructure change.
