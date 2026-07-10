# TASK-051 Work Prompt: v3 Dynamic Report Cards

Use this prompt to start `TASK-051` as the Frontend Implementer agent.

```text
You are the Frontend Implementer agent for Outlook Signals.

Task: TASK-051, implement the v3 dynamic report UI.
Branch: frontend/TASK-051-v3-report-cards.

Primary goal:
Replace the fixed v2 report-section rendering with the frozen ADR-033 v3
contract. Render the successful report as a card flow with exactly one visible
section at a time, while preserving report-specific data-as-of and
interpretation-caution context on desktop and mobile.

Start by reading, in order:
1. AGENTS.md
2. docs/prd/README.md and the linked PRD section files
3. docs/ux-design/README.md and its linked files
4. memory/project.md
5. memory/session.md
6. tasks/active.md, especially TASK-051 and the TASK-049/TASK-050/TASK-053
   coordination notes
7. prompts/implementation-frontend.md
8. memory/architecture.md
9. standards.md
10. memory/glossary.md
11. memory/decisions.md, especially ADR-032 and ADR-033; ADR-033 supersedes
    ADR-032 wherever their v3 content/display contracts differ
12. backend/API_CONTRACT.md, especially "Approved v3 report contract
    replacement" and "Approved Frontend section order and labels"
13. reports/day-5-v3-implementation-allocation.md
14. frontend/src/types/issue.ts
15. frontend/src/App.tsx
16. frontend/src/components/IssueReportCard.tsx
17. frontend/src/components/InformationNotice.tsx and
    frontend/src/components/cautionCopy.ts

Before implementation:
- Confirm TASK-051 is assigned to the Frontend Implementer and that its branch
  is frontend/TASK-051-v3-report-cards.
- Fetch the latest remote state. Create the task branch from the latest
  origin/main if it does not exist, or switch to the existing task branch and
  preserve any user-authored changes.
- Inspect whether TASK-050 has already landed. If it has not, implement against
  ADR-033 with typed local fixtures; do not wait for live v3 rows.
- TASK-050 owns Backend/Pydantic/API contract edits. Do not modify backend
  schemas, routes, API contract documentation, report generation, stored rows,
  migrations, or prompt-version selection in this task.
- Do not add a dependency, change infrastructure, deploy, call an external AI
  provider, write to a configured database, or read/print/edit secret files.
- Do not change the wording policy or the approved ADR-033 labels.

Frozen successful-response contract:

type IssueReportContent = {
  issue_overview: string;
  current_data_reading: string;
  possible_outlook: string;
  possible_drivers: string;
  external_context: string | null;
  what_to_check: string;
  data_limitations: string;
  caution_note: string;
};

type IssueReportSuccessResponse = {
  id: string;
  status: "success";
  report_version: "v3";
  generated_at: string;
  data_as_of: string;
  content: IssueReportContent;
};

The accepted empty response remains:

{ "status": "not_yet_generated" }

Required display order and approved Korean labels:
1. issue_overview — 이슈 개요
2. current_data_reading — 현재 데이터 읽기
3. external_context — 외부 맥락
4. possible_drivers — 변화와 함께 확인할 요인
5. possible_outlook — 조건부 전개
6. what_to_check — 추가 확인 사항
7. data_limitations — 데이터 한계
8. caution_note — 해석 주의

Implementation requirements:

1. Align the frontend response types exactly.
   - Replace the v2 content keys with the eight ADR-033 keys above.
   - Add the required top-level report_version: "v3" field.
   - Keep status="not_yet_generated" as the only non-success API response
     represented by IssueReportResponse.
   - Do not carry v1/v2 aliases or partially transform a legacy successful
     payload into v3.

2. Validate untrusted report JSON before it reaches the success UI.
   - Fetch the report payload as unknown and narrow it with a small local parser
     or type guard; a TypeScript cast alone is not runtime validation.
   - A success payload is valid only when its top-level fields are present,
     status is "success", report_version is "v3", and content has the exact
     eight-key set with no missing or extra key.
   - external_context is the only nullable content value. Hide it only when its
     value is exactly null.
   - Every other content value must be a non-empty string after trimming.
     Empty strings, whitespace-only strings, nulls, missing keys, unexpected
     value types, legacy keys, and extra keys must enter the existing isolated
     report error state. Never partially render them.
   - If frontend validation enforces ADR-033 length bounds, count trimmed
     Unicode code points with Array.from(value.trim()).length, not
     value.length. Use the exact bounds from backend/API_CONTRACT.md.
   - Keep a malformed report isolated from the issue detail/chart state; the
     rest of the detail page must remain usable.

3. Use one exhaustive section definition as the rendering source of truth.
   - Define the ordered mapping with as const and satisfies so keys and labels
     remain typed.
   - Add an explicit invariant or an existing-test-suite assertion that the
     mapping contains eight unique keys and exactly equals the frozen content
     key set. TypeScript satisfies alone does not prove exhaustiveness.
   - Do not add a test framework dependency. If no frontend test runner exists,
     keep the invariant in a dependency-free pure helper/runtime assertion and
     cover it through typecheck plus browser fixtures. If test infrastructure
     exists after rebasing, add focused tests there.

4. Build accessible one-section-at-a-time navigation.
   - Derive visible sections from the ordered mapping. Remove only
     external_context when its value is null; all other sections remain.
   - Initially show issue_overview. Keep exactly one section body visible to
     sighted users and assistive technology at a time.
   - Provide clear previous/next controls and a compact current-step indicator.
     Direct section controls are optional, but any control that is added must
     use semantic buttons, visible focus treatment, an accessible name, and a
     clear current/disabled state.
   - Navigation must use the filtered section count, so a null
     external_context produces a coherent seven-step flow with no blank step.
   - Reset or safely clamp the active section when the selected issue, report,
     or visible-section list changes.
   - Keep controls in stable locations. Labels and bodies must wrap naturally;
     do not use ellipsis, line clamping, horizontal scrolling, or fixed heights
     that clip text. Use a stable card/body layout or an equivalent technique
     so moving between brief and maximum-length sections does not cause abrupt
     control movement or unusable page jumps.

5. Keep report timing and caution semantics accurate.
   - For a successful report, use report.data_as_of as the report reference
     time and show report.generated_at separately.
   - Place a compact report-caution strip and the report data-as-of timestamp
     directly adjacent to current_data_reading on both mobile and desktop.
   - Keep the complete content.caution_note as the final navigable report
     section; it is never hidden.
   - ADR-033 does not add top-level confidence_level. Do not present the current
     issue object's CautionBadge as if it qualifies a stored report when the
     issue and report data_as_of timestamps differ. The report's caution_note
     is the snapshot-bound caution indicator.
   - Existing issue-level badges may remain on issue-level surfaces, but their
     scope must not be confused with the stored report.
   - Preserve nearby interpretation guidance for loading,
     not_yet_generated, malformed/fetch-failure, and success states.

6. Preserve existing non-success behavior without showing v2 content.
   - Keep neutral loading, not-yet-generated, and report-error states.
   - Keep any fallback summary visibly identified as a current-screen fallback,
     not as a stored v3 report.
   - Do not let report loading or failure block the issue detail, chart, or
     manually curated related-event area.
   - Review any changed user-facing string against standards.md and
     memory/glossary.md. Do not broaden the approved wording policy.

Expected frontend change surface:
- frontend/src/types/issue.ts
- frontend/src/App.tsx or a small dependency-free report parser/helper
- frontend/src/components/IssueReportCard.tsx
- focused fixture/helper files only when they materially improve verification

Keep the change local. Avoid unrelated refactors and do not modify Backend or
Data/AI files.

Required verification:
1. From frontend/ run:
   - npm run typecheck
   - npm run lint
   - npm run build
2. Exercise these successful-report fixtures without a live v3 DB row:
   - all eight fields with non-null external_context
   - external_context=null, producing seven visible sections
   - maximum-length/wrapping content for every section
3. Exercise invalid-response handling:
   - one missing required key
   - empty or whitespace-only required value
   - external_context=""
   - extra content key
   - legacy v2 success shape
   - wrong or missing report_version
4. Exercise existing loading, not_yet_generated, and fetch-failure states.
5. Browser-check at least 320px, 375px, and one desktop width:
   - only one section is visible
   - previous/next state and step count are correct
   - focus order and keyboard activation work
   - maximum-length Korean text and labels wrap without clipping or horizontal
     overflow
   - navigation controls stay usable while section content changes
   - report data-as-of and compact caution context remain adjacent to
     current_data_reading
   - the complete caution_note remains reachable as the final section
6. Run a targeted wording scan over changed user-facing strings and record the
   result. Policy documents and tests may reference blocked expressions only
   when defining or checking the rule; product copy must pass the shared lint.
7. Run git diff --check and inspect git diff before closeout.

Definition-of-done gate:
- Frontend types and runtime parsing match ADR-033 exactly.
- Sections use the frozen evidence-first order and Korean labels.
- external_context is hidden only for null; invalid required content enters the
  report error state.
- The one-visible-section card flow works accessibly on desktop and mobile
  without text overflow, clipping, or disruptive control movement.
- Report data-as-of and report-specific caution context remain accurate and
  nearby.
- Typecheck, lint, build, responsive browser checks, and wording checks pass.
- No dependency, schema, API, infrastructure, deployment, provider-call, or DB
  write boundary was crossed.

When finished:
- Update tasks/active.md status while working. Move TASK-051 to
  tasks/completed.md only when every definition-of-done item is met; otherwise
  leave it active and state the exact remaining work.
- Update memory/session.md and archive the session under memory/sessions/.
- Update memory/decisions.md, memory/known-issues.md, or memory/architecture.md
  only if the implementation creates a real decision, issue, or architecture
  change.
- Record verification commands, fixture states, viewport widths, wording-lint
  result, and any known TASK-050 integration dependency in the session handoff.
- Do not commit or push unless the user explicitly asks.
- Final response should name the main files changed, summarize the card-flow
  behavior, list verification results, and state any remaining TASK-050 or
  TASK-053 handoff.
```
