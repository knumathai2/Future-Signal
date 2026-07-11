# TASK-086 Exact Title Validation

Date: 2026-07-11
Owner: Data/AI Implementer
Status: Complete

The v5 semantic gate now requires `executive_summary` to contain the exact
source `market.title` once. Missing, whitespace-modified, and duplicated source
titles fail with `exact_title_occurrence_mismatch` after the existing genericity
check. Tests use exact case-sensitive source text and cover all failure shapes.

Verification: 181 focused Backend tests passed and Ruff is clean. No external
call or database write was performed.
