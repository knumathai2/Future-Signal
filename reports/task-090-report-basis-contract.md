# TASK-090 Report Basis Contract

Date: 2026-07-11
Owner: Backend + Data/AI + Frontend
Status: Complete

Every v5 scenario, factor, and later-material item now carries one strict basis:
`market_definition`, `observed_data`, `verified_context`, or `data_limitation`.
Generation and API reconstruction reject a definition basis without a stored
condition, verified-context basis without a verified candidate, or limitation
basis without a deterministic missing-field entry. Backend and Frontend schemas
forbid missing, unknown, or extra nested fields. The report card renders a
compact Korean evidence-range label for each item.

Verification:

- Related Backend suite: 195 passed.
- Basis adversarial unit suite: 94 passed.
- Ruff: passed.
- Frontend typecheck, strict parser, lint, and production build: passed.
- Existing bundle-size warning remains unchanged.

No external call or non-test database write was performed.
