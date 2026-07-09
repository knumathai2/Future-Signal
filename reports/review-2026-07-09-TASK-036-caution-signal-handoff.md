# Review: TASK-036 Caution Badge Logic and Signal Handoff

Date: 2026-07-09
Reviewer: Reviewer
Reviewed branch: `origin/data-ai/TASK-036-caution-signal-handoff` (`5cfd3b8`)
Base checked against: `origin/main` (`416e8a4`)
Verdict: Request Changes

## Correctness and Safety Findings

- [P1] `origin/data-ai/TASK-036-caution-signal-handoff` is not merge-ready against
  current `origin/main`. The branch is 17 commits behind and conflicts in
  `memory/decisions.md`, `memory/known-issues.md`, `memory/session.md`, and
  `tasks/completed.md`. It also adds a new `ADR-016` at
  `memory/decisions.md:239`, but current main already uses `ADR-016` for
  TASK-009 signal detection. The branch session handoff also says to continue
  TASK-009 at `memory/session.md:47`, while current main already records
  TASK-009 as completed in `tasks/completed.md:27`. Rebase onto current main,
  renumber the new ADR, and refresh the handoff notes before merge.

- [P2] `git diff --check` fails from trailing whitespace in
  `backend/app/core/snapshot_metrics.py:313`,
  `backend/app/core/snapshot_metrics.py:317`, `memory/decisions.md:246`, and
  `memory/session.md:23`, plus a final blank-line issue in
  `memory/decisions.md`. This is mechanical but should be fixed before review
  approval.

No product-safety blocker was found in the metric logic itself.
`insufficient_data` still takes precedence before low-activity or
high-volatility checks in `backend/app/core/snapshot_metrics.py:311`.
The caution logic uses only existing schema/API fields:
`market_metrics.confidence_level`, `volume_24h`, `liquidity`, and `change_24h`.
No schema migration, public API expansion, free-form analysis generation,
automated external event matching, wallet-level feature, or participant-level
feature was introduced.

## Focus Checks

- Caution-level logic uses existing fields: pass. The code extends
  `compute_confidence_level` and passes existing snapshot liquidity through
  `build_metric`; no new model/schema/API fields are added.
- Insufficient history behavior: pass. Missing 24h or 7d reference still returns
  `insufficient_data` rather than computed-looking values.
- Low-activity and high-volatility thresholds: partially pass. Thresholds are
  documented in code and ADR text as conservative hardcoded MVP constants:
  `volume_24h < 500`, `liquidity < 1000`, and `abs(change_24h) > 15pp`.
  Remaining tuning risk is noted below.
- 5pp expectation-shift threshold: pass on current main. TASK-036 does not alter
  the detector. Current `backend/tests/test_signal_detection.py` still covers
  threshold and cooldown behavior.
- Marker handoff notes: needs rebase cleanup. The intended payload
  (`signal_type`, `severity`, `window`, `magnitude`, `triggered_at`) matches
  the accepted `IssueDetail.signals` shape, but the branch ledger predates the
  merged TASK-009/TASK-010 state and must be reconciled.

## Validation

- Metric tests: `backend/tests/test_snapshot_metrics.py` covers sufficient,
  insufficient, low-activity, and high-volatility paths in
  `test_compute_confidence_level`.
- Signal tests: current main's `backend/tests/test_signal_detection.py` covers
  below-threshold, at/above-threshold, insufficient/null skip, and cooldown
  behavior.
- Commands run:
  - `pytest backend/tests/test_snapshot_metrics.py -q` in TASK-036 worktree:
    20 passed.
  - `pytest backend/tests -q` in TASK-036 worktree: 42 passed.
  - `ruff check backend/app/core/snapshot_metrics.py backend/tests/test_snapshot_metrics.py`:
    passed.
  - `pytest backend/tests/test_signal_detection.py -q` on current main:
    14 passed.
  - `git diff --check origin/main...origin/data-ai/TASK-036-caution-signal-handoff`:
    failed with whitespace issues listed above.

## Remaining Risks

The low-activity thresholds are intentionally conservative but broad: in the
current 50-record normalized sample, `volume_24h < 500` flags 22 markets and
`liquidity < 1000` flags 4. The high-volatility state is currently a `>15pp`
24h-change proxy, not a true volatility calculation. That is acceptable for MVP
if documented, but it should be tuned once real batch history exists.
