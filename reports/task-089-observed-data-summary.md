# TASK-089 Observed-data Summary

Date: 2026-07-11
Owner: Data/AI Implementer
Status: Complete

The v5 observed-data JSON now includes 24-hour activity, liquidity, a
deterministic seven-day history summary, and an explicit missing-field list.
The backend computes chronological start/end values, extrema, and sample count
from append-only snapshots. Pydantic validates time ordering, range ordering,
and endpoint containment. API reconstruction reloads the same fixed metric-time
window, so later snapshots cannot change an older report's evidence.

Verification: 194 focused Backend tests passed and Ruff is clean. Tests cover
deterministic ordering, extrema, sample count, prompt serialization, missing
fields, batch query behavior, and API reconstruction. No external call or
non-test database write was performed.
