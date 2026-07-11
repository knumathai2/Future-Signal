# TASK-101: Proposed v7 positive-first briefing contract

Date: 2026-07-11  
Owner: PM / Data-AI  
Branch: `data-ai/TASK-101-v7-briefing-contract`  
Status: Approval-ready proposal; not active

## 1. Scope and activation boundary

This document finalizes the proposed writer, evidence, and source-level
contract required before implementation. It does not amend the current
constitution, active v6 policy, source-publication gate, API, schema, batch
workflow, or provider configuration.

Activation requires explicit approval of TASK-099 approval items 1 and 2:

1. replace the active negative-first v6 writer policy with the positive-first
   v7 evidence policy; and
2. permit accepted A-C source levels with visible attribution instead of the
   current universal independently verified publication gate.

## 2. Responsibility split

### Writer-owned output

The model returns only:

```json
{
  "headline": "string",
  "summary": "string",
  "sections": [
    {
      "type": "issue_overview",
      "title": "string",
      "format": "paragraph",
      "content": "string",
      "items": [],
      "evidence_refs": ["market_definition:revision-id"]
    }
  ]
}
```

### Backend-owned output

The model never creates or changes:

- report, request, issue, metric, definition, context, or source identifiers;
- observed values, changes, timestamps, cache state, or input fingerprint;
- source URL, title, domain, publication time, retrieval time, or source level;
- supported-claim records;
- report version, generation status, caution text, or data limitations; or
- last-known-good selection.

The generation service resolves the writer's references against the exact
input bundle, reconstructs public source records, and assembles the final v7
envelope.

## 3. Writer schema

### Top-level bounds

| Field | Contract |
|---|---|
| `headline` | non-empty Korean-oriented text, 10-120 Unicode characters |
| `summary` | 40-900 Unicode characters |
| `sections` | 2-8 sections; order selected by the writer |

### Section contract

| Field | Contract |
|---|---|
| `type` | one of `issue_overview`, `current_context`, `market_data`, `external_context`, `uncertainties`, `what_to_watch` |
| `title` | 2-100 Unicode characters |
| `format` | `paragraph` or `bullets` |
| `content` | 30-1800 characters for `paragraph`; otherwise `null` |
| `items` | 1-8 items of 15-500 characters for `bullets`; otherwise empty |
| `evidence_refs` | 1-12 unique references; every factual section must identify its support |

The writer may omit unavailable categories, choose section order, and choose
paragraph or bullets. It must include at least one `issue_overview` or
`current_context` section. It may include at most one `market_data` section
because deterministic observed values are rendered separately and should not
be repeated across several authored sections.

### Evidence reference grammar

The input bundle supplies opaque references using only these prefixes:

```text
market_definition:<revision-id>
metric:<metric-id>
observed_history:<metric-id>
context:<context-id>
source:<source-id>
data_limitation:<code>
```

The writer copies references; it cannot create new IDs. `source:` references
must be accompanied by their parent `context:` reference. Facts about a source
must reference that exact source. Market values must reference `metric:` or
`observed_history:` and are replaced or verified by deterministic assembly.

## 4. Positive-first prompt

The proposed system prompt is:

```text
You are an issue briefing writer helping a general reader understand the
current issue quickly and accurately.

Begin by explaining what the issue is and why its stated condition matters.
Summarize the current situation using the supplied source material. Explain
the observed market-data movement in clear language while keeping market
observations and external-source information visibly distinct. Connect every
factual statement to the supplied evidence reference that supports it.

When the material supports more than one interpretation, present the
alternatives and explain what remains uncertain. Attribute statements to their
source when the source level or evidence requires attribution. Tell the reader
which announcements, documents, dates, or data updates would help clarify the
issue next.

Use natural, concrete Korean. Choose the number, order, titles, and paragraph
or bullet presentation of sections according to the available evidence. Omit
a category when no supplied evidence supports it. Return only the requested
JSON object.

Do not invent facts, sources, references, relationships, or future results.
Do not encourage the reader to take a financial or market action. Treat an
observed timing overlap as timing unless a supplied source explicitly supports
a stronger attributed statement.
```

Unlike v6, the prompt does not prohibit all authored dates, numbers, proper
names, English terms, or source-supported current facts. Those are allowed when
an exact evidence reference supports them. Deterministic validation, not a long
negative instruction list, enforces evidence and public-shape integrity.

## 5. Source-level policy

| Level | Classification | Public use | Attribution | Default verifier behavior |
|---|---|---|---|---|
| A | Official record, primary document, direct institutional statement | Direct facts and statements contained in the source | Name the issuing body or document | No model call when access, identity, relevance, time, and claim support are deterministic and conflict-free |
| B | Established reporting or recognized specialist/public institution | Current context and source-supported synthesis | Name the publisher or institution for material claims | Call only for ambiguity, conflict, high-impact claim, strong relationship language, or uncertain support |
| C | Relevant single-source or supporting material that passes access, identity, relevance, time, and claim checks | Supporting context only; cannot be presented as universally established | Always visibly attribute the claim and retain level C | Same conditional triggers; a model cannot upgrade C to A/B |
| D | Inaccessible, unsafe, unrelated, generated without usable provenance, duplicated without added support, or materially unsupported | Never public | Internal audit only | No promotion path |

### Deterministic checks for A-C

Every accepted source must pass:

1. safe canonical HTTP(S) URL and accessible content;
2. source identity and level classification from deterministic domain/document
   rules plus stored metadata;
3. issue, named-entity, and condition relevance;
4. publication/effective time and retrieval time capture;
5. one or more explicit supported claims;
6. duplicate/syndication detection; and
7. no unresolved contradiction with stronger accepted evidence.

A model may withhold a source or narrow its supported claims. It cannot create
a source, change a level, bypass a failed deterministic check, or promote D.

### Conditional verifier triggers

A separate no-search verifier is required when any of these is true:

- two accepted sources materially conflict;
- entity, condition, or temporal relevance is ambiguous;
- a claim concerns an announced, completed, or legally effective high-impact
  event;
- proposed prose uses a causal or outcome-conclusive relationship;
- a level-C claim would materially shape the briefing summary; or
- deterministic claim extraction cannot map the prose to a bounded excerpt.

Verifier unavailability fails only the affected candidate or claim closed. It
does not stop market collection and does not erase previously accepted context.

## 6. Validation matrix

### Publication blockers

| Rule | Required action |
|---|---|
| Invalid or extra writer fields | Reject the generation result |
| Missing, unknown, mismatched, or forged evidence reference | Reject the generation result |
| Source fact not supported by the exact stored claim/excerpt | Reject the generation result |
| Invented or altered URL, title, metric, date, entity, source level, or timestamp | Reject the generation result |
| Material contradiction with referenced evidence | Reject the generation result |
| Unattributed level-C material claim | Reject the generation result |
| Unsupported future-result or causal assertion | Reject the generation result |
| Direct reader inducement outside information briefing | Reject the generation result |
| Unsafe public link or irreconstructible public envelope | Reject the generation result |

On rejection, append a safe failure audit record when the request schema is
available and preserve the last valid report. Do not retry the same input and
prompt automatically.

### Quality diagnostics

These produce metrics or reviewer warnings, not automatic total rejection,
unless they make the output unusable or violate a blocker above:

- moderate repetition or section overlap;
- section order or count preference;
- English terms, sentence length, or stylistic awkwardness;
- generic but factually supported prose;
- paragraph versus bullets choice; and
- conditional-language preference where no factual overstatement results.

## 7. Exact proposed policy supersessions

If approved, TASK-101 supersedes these active v6 rules for new v7 generation:

- the four deterministic report-mode unions;
- mandatory basis labels on each authored item;
- the blanket authored digit/date/deadline ban;
- the non-anchor English ban;
- exact scenario-to-material cardinality;
- fixed conditional-token requirements;
- hard rejection for ordinary section duplication or genericity; and
- universal independent-model verification before any source becomes public.

It does not supersede aggregate-only data, evidence reconstruction, safe URLs,
append-only history, honest timestamps, interpretation caution, non-causality,
non-prediction, last-known-good behavior, or the current prohibited
product-language policy. Any wording-policy amendment must be recorded in the
active glossary/standards/constitution during approved activation.

## 8. Implementation handoff

After approval:

1. add v7 Pydantic writer models and fake-client tests without yet exposing a
   public endpoint;
2. add deterministic reference resolution and claim-support validation;
3. update context policy/version models for A-D levels and conditional verifier
   routing in TASK-103;
4. store writer prompt/policy/input-schema versions in the request fingerprint;
5. keep v6 readers available until TASK-105 changes the public contract; and
6. carry the blocker/diagnostic split into TASK-107 acceptance tests.

No provider call, database write, dependency, schema, API, workflow,
infrastructure, deployment, or production action is authorized by this draft.
