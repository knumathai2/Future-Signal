# TASK-082 Grounding Contract

Date: 2026-07-11
Owner: Data/AI Implementer
Status: In progress

## Purpose

Define the evidence, completeness, output, validation, and rollout contract for
the AI-report grounding program before any database schema or public API change
is implemented. This task does not authorize a migration, database write, paid
provider call, deployment, or public API change.

## Evidence classes

The collector stores the exact market question but replaces the source market
description with a generic display-safe sentence. The program must therefore
keep these evidence classes separate:

1. `market_definition`: source question and resolution rules.
2. `observed_data`: stored measurement values and timestamps.
3. `verified_context`: independently verified citation-backed material.
4. `data_limitation`: explicit missing fields and coverage limits.

## Resolution-rules contract

`resolution_rules` is internal structured evidence, separate from the
user-facing `market.description`.

| Field | Type | Required | Source | Missing-value behavior |
|---|---|---:|---|---|
| `condition_text` | `string | null` | No | Exact source market description or a provenance-preserving normalized copy | Null; issue-specific procedural scenarios are not permitted |
| `deadline` | `datetime | null` | No | Market `endDate`, unless an explicit source rule supplies a different deadline | Null; deadline claims are not permitted |
| `exclusions` | `string[]` | Yes | Explicit exception clauses from the source rule | Empty; no exclusions may be inferred |
| `resolution_source` | `string | null` | No | Source `resolutionSource` URL | Null; no official-domain status is inferred |
| `source_description_hash` | `string | null` | No | Deterministic hash of the stored source description | Null when no source description exists |
| `collected_at` | `datetime` | Yes | Collector run timestamp | Input is invalid when absent |

The implementation must preserve source evidence internally without exposing
it as display copy. It must not derive an exclusion, procedural stage,
institution, or official-source classification from the market title alone.

## Input completeness contract

| Level | Conditions | Permitted output |
|---|---|---|
| `definition_complete` | `condition_text` exists and available deadline/exclusions are captured | One to four distinct scenarios grounded in the definition and verified evidence |
| `definition_partial` | `condition_text` exists but referenced rule material is absent | One to three scenarios limited to the available condition; missing material is named |
| `definition_missing_with_context` | No `condition_text`; at least one verified candidate exists | No procedural or resolution claim; one or two items may state what cited material records and what definition is missing |
| `definition_missing_no_context` | No `condition_text`; no verified candidate | Exactly one limitation scenario; no institution, procedure, event, or outcome path may be introduced |

Completeness is computed deterministically before the model call. The model
does not choose or upgrade the level.

## Output contract

### Immediate validation without a public API change

- `executive_summary` contains the exact `market.title` once.
- Unsupported numbers, URLs, dates, and title-independent generic summaries
  remain blocked.
- A procedural noun, institution, event, or condition that cannot be tied to
  an available evidence class is rejected.

### Approval-gated public contract

- `conditional_scenarios` changes from three-to-four items to one-to-four.
- Scenario, factor, and later-material items gain a `basis` enum:
  `market_definition`, `observed_data`, `verified_context`, or
  `data_limitation`.
- `verified_context` is invalid when no verified candidate is present.
- `market_definition` is invalid when `condition_text` is null.

Claim-level UUID references remain a later extension. The MVP program uses the
bounded `basis` enum first.

## Observed-data extension

The writer input later adds deterministic values only:

```json
{
  "value_24h_ago": null,
  "value_24h_ago_at": null,
  "value_7d_ago": null,
  "value_7d_ago_at": null,
  "volume_24h": null,
  "liquidity": null,
  "recent_history_summary": {
    "start_at": null,
    "start_value": null,
    "end_at": null,
    "end_value": null,
    "min_value": null,
    "max_value": null,
    "sample_count": 0
  },
  "missing_fields": []
}
```

The backend, not the model, computes comparison values, extrema, and sample
counts. A comparison value and timestamp are either both present or both null.
Stored changes must match selected reference values within database precision.

## Evaluation cases

The program covers these six cases without calling an external model:

1. Legislative title/value only: one limitation scenario; no unsupported
   committee, chamber, schedule, identifier, or procedural stage.
2. Monetary-policy title/value only: one limitation scenario; no unsupported
   bank, meeting, policy setting, indicator, or decision path.
3. Diplomatic title/value only: one limitation scenario; no unsupported party,
   mediator, document, effective period, or negotiation state.
4. Complete legislative resolution rule: scenarios use only supplied
   recognition and exclusion clauses.
5. Complete monetary-policy resolution rule: scenarios use only the supplied
   meeting, measurement definition, and deadline.
6. Complete diplomatic resolution rule plus verified context: definition,
   observed values, and cited material stay separate and no relationship is
   established between them.

Every case verifies strict JSON parsing, exact title occurrence, allowed
scenario count, unsupported-claim rejection, valid `basis` availability,
stored-data framing, and non-duplicated issue-specific prose.

## Task sequence and gates

| Task | Scope | Gate |
|---|---|---|
| TASK-083 | New append-only resolution-rule storage and normalization | Explicit database-schema approval before implementation |
| TASK-084 | Resolution rules in writer and research inputs | TASK-083 verified |
| TASK-085 | One-to-four scenarios and completeness-aware generation | Explicit public-API approval before implementation |
| TASK-086 | Exact-title deterministic validation | TASK-084 verified |
| TASK-087 | Real zero-evidence API/UI regression | TASK-085 verified |
| TASK-088 | Reference values/timestamps and consistency validation | TASK-084 verified |
| TASK-089 | Activity, liquidity, and deterministic history summary | TASK-088 verified |
| TASK-090 | `basis` enum in stored/public/UI contracts | Explicit public-API approval; TASK-085 and TASK-089 verified |
| TASK-091 | Full integration, safety, copy, and scope audit | All predecessors verified |

## Completion criteria

- Resolution-rule provenance and missing-value behavior are fixed.
- Deterministic completeness levels control allowed output richness.
- The lightweight `basis` vocabulary is fixed.
- Six evaluation cases and their assertions are fixed.
- Schema and API changes remain behind explicit approval gates.
- No product code, migration, database, provider, or deployment is changed.
