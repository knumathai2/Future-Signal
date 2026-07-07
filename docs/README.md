<!--
Purpose:        Index for authoritative product-spec documents inside the Harness root
Owner:          PM
Update Trigger: Product spec section split, renamed, or moved
Harness Version: 1.1
-->

# docs/ — Outlook Signals Product Specs

`AI Development Harness/` is the working root for this project. The authoritative product specifications now live inside this `docs/` directory, split by source document and section range.

## Canonical Spec Entrypoints

- [PRD](prd/README.md) — product requirements, MVP scope, 5-day schedule, presentation strategy, and copy.
- [Service Design](service-design/README.md) — Polymarket data collection, metrics, AI I/O design, signal design, and participant-analysis policy.
- [Technical Design](tech-design/README.md) — stack, architecture, DB schema, API contract, batch pipeline, and AI prompt design.
- [UX Design](ux-design/README.md) — screen flow, copy policy, gambling-pattern removal plan, disclaimer strategy, and prohibited-feature policy.

## Authority

The harness process files (`AGENTS.md`, `ORCHESTRATOR.md`, `standards.md`, `tech-stack.md`, `dependencies.md`, `roadmap.md`, `memory/`, `tasks/`, `prompts/`) govern how the team works. The product spec files linked above govern what the product is. When product scope and process guidance conflict, use the relevant spec index here to find the source section, then update the process file to match.
