# TASK-092 — v6 Evidence-Aware Briefing Policy

Date: 2026-07-11  
Owner: PM / Planner  
Branch: `pm/TASK-092-evidence-aware-briefing-policy`  
Status: approved; TASK-092 complete

## 1. Product outcome

V6 stops using the same metric and resolution-rule language in several briefing
cards. Deterministic code selects one of four briefing modes from two independent
facts: whether the linked metric contains a significant observed change and
whether at least one public context candidate passes the existing strict
verification/read gates.

The model receives only the fields allowed by the selected mode. Current value,
change magnitude, reference date, and resolution rules are deterministic data,
not model-authored prose. Resolution rules move to a collapsed reference
disclosure labelled `판정 기준 보기`.

## 2. Deterministic decision table

| Significant observed change | Verified material | `report_mode` | Briefing order |
|---|---|---|---|
| yes | yes | `change_with_evidence` | observed change → verified background → conditional interpretation → exact source links |
| yes | no | `change_without_evidence` | observed change → fixed no-verified-background state → general conditional scenarios → materials to check |
| no | yes | `stable_with_evidence` | issue explanation → verified public background → conditional scenarios → exact source links |
| no | no | `stable_without_evidence` | general issue explanation → general conditional scenarios → materials to check |

The stable modes must not describe a below-threshold or unavailable change as a
notable movement. The no-evidence modes must not create a current event, source,
person status, procedure, or relationship that is absent from supplied evidence.

## 3. Decision rules

### 3.1 Significant observed change

`has_significant_change` is true exactly when the latest linked
`market_metrics` row would produce the existing MVP `expectation_shift` signal:

- `confidence_level != "insufficient_data"`;
- `change_24h` is non-null; and
- `abs(change_24h) >= 0.05` on the stored 0–1 scale (at least 5 percentage
  points).

This reuses `build_expectation_shift_signal()` and
`EXPECTATION_SHIFT_THRESHOLD`; a persisted signal row is supporting audit
evidence, not a second mode-selection rule. This avoids cooldown suppressing a
mode that the linked metric still qualifies for. A null change or insufficient
data selects a stable mode and remains explicitly limited in the caution copy.

### 3.2 Verified material present

`has_verified_evidence` is true only when one to three candidates remain after
the current v5 read-time reconstruction rules:

- same market and compatible stored episode;
- `verification_state="verified"` and not expired at report generation;
- deterministic provenance/date/entity/condition/source gates passed;
- independent different-provider verification passed;
- at least one stored citation source with exact title, URL, domain,
  publication time when available, and allowed source type; and
- URL/domain/timing/evidence-reference consistency passes again on read.

Withheld, rejected, expired, malformed, source-less, timing-mismatched, or
otherwise non-public candidates count as zero. Candidate count never comes from
model prose.

## 4. Evidence basis and authored-field contract

V6 adds a strict evidence-basis enum:

- `observed_data`: deterministic metric/snapshot content only;
- `market_definition`: bounded issue explanation from stored market metadata;
- `verified_context`: statements supported by the returned verified candidate
  IDs and exact stored sources;
- `general_scenario`: a clearly labelled general conditional explanation that
  does not claim to describe the current situation; and
- `data_limitation`: missing or limited evidence stated without filling the gap.

Every authored block or nested item carries exactly one basis. A basis is valid
only when its corresponding input class exists. `general_scenario` is allowed
only in a mode that calls for general explanation or scenarios and must be
displayed with this meaning:

> 현재 상황을 입증하는 검증 자료가 아니라 일반적인 시나리오 설명입니다.

External knowledge may appear only when the response can expose its source and
evidence type through an already verified candidate. Without that structure,
the writer is limited to stored market metadata and may not add a current event,
named-person state, concrete procedure, or recent factual claim.

## 5. Exact v6 public response proposal

The endpoint remains `GET /api/issues/{id}/report`. It changes from the v5 body
to a v6 discriminated response:

```json
{
  "id": "uuid",
  "status": "success",
  "report_version": "v6",
  "report_mode": "stable_without_evidence",
  "generated_at": "2026-07-11T09:05:00Z",
  "data_as_of": "2026-07-11T09:00:00Z",
  "episode_at": "2026-07-11T09:00:00Z",
  "observed_change": {
    "metric_id": 123,
    "window": "24h",
    "current_value": 0.055,
    "change_value": 0.0,
    "significant": false,
    "threshold": 0.05
  },
  "briefing": {
    "mode": "stable_without_evidence",
    "issue_explanation": {
      "text": "...",
      "basis": "market_definition"
    },
    "conditional_scenarios": [
      {"title": "...", "text": "...", "basis": "general_scenario"}
    ],
    "materials_to_check": [
      {"title": "...", "text": "...", "basis": "general_scenario"}
    ]
  },
  "resolution_reference": {
    "status": "available",
    "condition_text": "...",
    "deadline": "2026-12-31T00:00:00Z",
    "exclusions": [],
    "source_url": null
  },
  "evidence_refs": ["metric:123"],
  "context_candidates": [],
  "data_limitations": "...",
  "caution_note": "..."
}
```

The `briefing` field is a strict discriminated union:

| Mode | Allowed authored fields |
|---|---|
| `change_with_evidence` | `verified_background`, `conditional_interpretations` |
| `change_without_evidence` | `conditional_scenarios`, `materials_to_check` |
| `stable_with_evidence` | `issue_explanation`, `verified_background`, `conditional_scenarios` |
| `stable_without_evidence` | `issue_explanation`, `conditional_scenarios`, `materials_to_check` |

`verified_background` uses only `verified_context`. General scenarios and their
check items use `general_scenario`. Issue explanation uses
`market_definition`. The no-verified-background message, general-scenario
notice, metric copy, limitations, caution, and resolution-reference labels are
deterministic UI/backend copy rather than writer output.

`resolution_reference.status` is `available` only for a validated stored rule;
otherwise it is `unavailable` with null rule fields. The API never derives a
missing rule from model prose. Existing v1–v5 rows remain audit-only. If a newer
v6 row fails, only an earlier contract-compatible v6 row may be returned.

## 6. Section ownership and non-duplication rules

| Information | Single owner |
|---|---|
| current value, 24h change, metric time, 5pp classification | `observed_change` |
| issue-level plain explanation | `briefing.issue_explanation` where allowed |
| verified current background | `briefing.verified_background` plus candidate/source cards |
| conditional implications | the mode-specific scenario/interpretation list |
| materials that could clarify a scenario | `materials_to_check` |
| exact resolution condition/deadline/exclusions | collapsed `resolution_reference` only |
| relationship boundary, data limits, caution | deterministic footer fields only |

The frontend renders the current value/change summary once in a dedicated
observed-change region. Model-authored text may not repeat a current value,
change amount, threshold, metric date, or resolution condition. Exact sources
appear once under verified background; cards may show source metadata and links
but may not repeat the background paragraph.

Generation and read paths both reject:

1. canonical exact duplicates after Unicode NFKC, case, punctuation,
   whitespace, number/unit, and date normalization;
2. body duplicates whose headings differ but normalized bodies match;
3. cross-section near-duplicates with at least four content tokens and token
   Jaccard similarity at or above 0.82;
4. authored numeric/date tokens that restate the deterministic metric fields;
5. resolution-rule sentence reuse or high-overlap rule paraphrase; and
6. repeated candidate/source claims not bound to the returned candidate IDs.

## 7. UI contract

- Render only the sections allowed by `report_mode`, in the decision-table
  order.
- Do not reserve a large empty verified-background region in no-evidence modes.
- Distinguish `verified_context` and `general_scenario` visually and in
  accessible text.
- Put the exact general-scenario notice next to the first general block.
- Render `판정 기준 보기` as a native disclosure or equivalent control,
  collapsed by default, keyboard operable, with `aria-expanded` and a visible
  focus state.
- Open only exact stored source URLs in a new tab with `noopener noreferrer`.
- Preserve data-as-of and interpretation caution in the same report surface.
- Reject mode/field/basis/evidence mismatches in the strict frontend parser.

## 8. Approval boundary

No schema change or new dependency is proposed. V6 reuses append-only
`ai_reports.content`, existing context tables, and existing resolution-rule
records.

The user explicitly approved the following scopes on 2026-07-11:

1. the AI policy change that permits clearly labelled, source-free general
   scenario explanation within the limits above; and
2. the public report API change from v5 to the exact v6 mode/evidence/reference
   contract above.

TASK-094 may change CLI fail-closed behavior after TASK-092, but adding or
changing workflow/runtime configuration (including the verifier-model setting)
requires a separate infrastructure approval. No deployment, production write,
existing-migration edit, new dependency, or wording-policy change is included.

## 9. Task handoff

- TASK-093: implement mode selection, typed model inputs/outputs, strict
  duplication/rule-leak/fact gates, and v6-only last-good storage.
- TASK-094: make incomplete requested context configuration an explicit failed
  outcome and add missing-verifier CLI regression coverage; stop before workflow
  mutation without approval.
- TASK-095: implement strict v6 reconstruction, exact source/reference output,
  OpenAPI, and integration coverage after API approval.
- TASK-096: implement the mode-specific UI, single metric region, disclosure,
  strict parser, responsive and accessibility states.
- TASK-097: run guarded development regeneration/evaluation within the existing
  cumulative budget and include the Trump-resignation regression.
- TASK-098: independently review all modes, data/source consistency, safety,
  duplication, fallback, responsive/accessibility behavior, and actual screen.
