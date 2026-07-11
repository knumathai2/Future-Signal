# TASK-084 Resolution Rules Input

Date: 2026-07-11
Owner: Data/AI Implementer
Status: Complete

## Result

- Added strict `ResolutionRulesInput` to the grounded report input.
- Added `market.resolution_rules` to the actual v5 writer JSON.
- Updated the v5 prompt to treat this object as the only source for conditions,
  deadlines, exceptions, and recognized source criteria.
- Stored the exact rule snapshot with each new v5 payload so read-time
  reconstruction validates against the same evidence used at generation time.
- Updated context research to prefer the latest stored condition and deadline,
  pass exclusions, pass the source URL, and derive an allowed domain only from
  that URL.
- Kept title-only fallback when no stored condition exists; generic display
  description is no longer used as a tracked condition.

No external API call, migration application, or non-test database write was
performed.

## Verification

```text
220 focused backend tests passed
Ruff: all checks passed
```

Coverage includes writer JSON serialization, stored-payload reconstruction,
legacy rows without rules, latest-rule research selection, official-domain
anchoring, exclusions, and existing v5 API behavior.
