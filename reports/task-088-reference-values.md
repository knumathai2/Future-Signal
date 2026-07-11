# TASK-088 Reference Values and Timestamps

Date: 2026-07-11
Owner: Data/AI Implementer
Status: Complete

The report input now carries the exact 24-hour and 7-day reference values and
timestamps selected by the same at-or-before-boundary rule used by metric
calculation. The Pydantic input contract requires value/time pairs and rejects
a stored change that cannot be reproduced within database precision. Writer
JSON exposes the four fields, and API read-time reconstruction reloads the
reference snapshots from the database.

Verification: 193 focused Backend tests passed and Ruff is clean. Tests cover
boundary selection, prompt serialization, missing pairs, inconsistent deltas,
legacy missing references, and API reconstruction. No external call or
non-test database write was performed.
