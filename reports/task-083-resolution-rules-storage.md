# TASK-083 Resolution Rules Storage

Date: 2026-07-11
Owner: Backend Implementer + Data/AI Implementer
Status: Complete

## Result

- Added the unapplied append-only migration
  `backend/migrations/003_market_resolution_rules.sql`.
- Added the matching `MarketResolutionRule` ORM model with per-market rule-hash
  idempotency and collection-time ordering.
- Preserved exact source condition text, deadline, source URL, description hash,
  rule hash, and collection time in live normalized collector return values.
- Kept exclusions empty instead of deriving clauses heuristically.
- Kept the existing checked/local normalized artifact display-safe by removing
  the internal `resolution_rules` object before JSON serialization.
- Appended a new rule version during snapshot preparation only when its rule
  hash differs from existing evidence.

No migration was applied and no database outside the in-memory test database
was touched.

## Verification

```text
python3 -m pytest -q backend/tests/test_collector_contract.py backend/tests/test_snapshot_metrics.py
25 passed

python3 -m ruff check backend/app/core/collector.py backend/app/core/snapshot_metrics.py backend/app/db/models.py backend/tests/test_collector_contract.py backend/tests/test_snapshot_metrics.py
All checks passed
```

Tests cover exact source preservation, display-safe artifact serialization,
source URL preservation, no inferred exclusions, append-only changed-rule
storage, duplicate-rule idempotency, and compatibility with the existing
normalized artifact whose historical rows do not yet contain rules.
