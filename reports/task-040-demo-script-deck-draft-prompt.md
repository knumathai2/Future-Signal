# TASK-040 Work Prompt: Demo Script and Deck Draft

Use this prompt to start `TASK-040` as the PM / Planner agent.

```text
You are the PM / Planner agent for Outlook Signals.

Task: TASK-040, Day 4 demo script and deck draft.
Branch: pm/TASK-040-demo-script-deck-draft.

Primary goal:
Create a Day 4 presentation deck outline and demo script draft so Day 5 can
focus on rehearsal, final screenshot capture, deployment readiness, and Q&A.

Start by reading, in order:
1. AGENTS.md
2. docs/prd/README.md and the linked PRD section files
3. docs/ux-design/README.md, especially copy/safety guidance
4. docs/service-design/README.md, especially AI output and participant policy
5. docs/tech-design/README.md, especially metrics, API, and report architecture
6. memory/project.md
7. memory/session.md
8. tasks/active.md
9. prompts/planning.md
10. reports/day-4-work-allocation.md
11. standards.md and memory/glossary.md

Before writing:
- Confirm the active task row for TASK-040: owner, assignee, branch, and status.
- Check whether the current branch includes the latest Day 4 updates such as
  v2 issue-explainer reports, Korean issue display labels, broad Korean category
  filters, and current-prompt report reads. Reflect only what exists in the
  branch or is clearly recorded in current memory.
- Do not add dependencies, change schemas, change public API shape, deploy,
  modify infrastructure, call paid external services, write to any shared DB, or
  print or edit secret files.
- Do not change the wording policy. Reference standards.md and
  memory/glossary.md instead.

Create or update this task output:
- reports/task-040-demo-script-deck-draft.md

The output must include:
1. A 7-10 slide deck outline covering:
   - title and one-line product frame
   - problem
   - limits of news, social feeds, and slow reports
   - product idea and core user flow
   - live/demo flow storyboard
   - implementation realism: data, API, chart, report, fallback path
   - safeguards: data-as-of timing, interpretation-caution text, aggregate-only
     handling, manual context candidates, template-constrained report generation
   - Day 5 finalization checklist
   - likely judge Q&A points
2. A 3-5 minute demo script following this exact spine:
   Home -> Detail -> Chart -> Summary -> caution notice -> manual context
   candidate.
3. A fallback narration for local/live data unavailability. It must clearly say
   when fallback data is being used, keep the data-as-of frame, and never imply
   that missing live data was refreshed successfully.
4. A screenshot and rehearsal checklist for Day 5.
5. A compact risk-response section for:
   - data representativeness
   - causal overreading
   - AI/report wording
   - 5-day build realism
   - static fallback readiness

Framing rules:
- Present Outlook Signals as an issue-monitoring and interpretation-support
  dashboard.
- Describe public Polymarket data as reflected expectation data from
  participants in that venue, not as the judgment of the public at large.
- Describe manually linked events only as context candidates, not causes.
- Do not assert future outcomes.
- Do not suggest reader action.
- Keep every data-bearing screen in the demo paired with a data-as-of timestamp
  and interpretation-caution context.
- Keep P1/P2 features as next-step story only; do not pull them into MVP scope.

Copy safety:
- Run a basic wording check on every deck/demo line you write against
  standards.md and memory/glossary.md.
- Record the check result inside the TASK-040 report.
- Leave the comprehensive cross-surface pass to TASK-018, but do not hand off
  obvious wording issues.

Suggested report structure:

# TASK-040: Day 4 Demo Script and Deck Draft

## Context Checked
- Files read
- Current implementation assumptions
- Any branch/memory mismatch

## Deck Outline
- Slide number, title, purpose, key speaking point, visual needed

## Demo Script
- Timebox
- Presenter narration
- Screen/action cue
- Safety/caution cue

## Fallback Narration
- Backend/API unavailable
- Report unavailable
- Chart history insufficient

## Screenshot and Rehearsal Checklist
- Required screenshots
- Required local/live checks
- Day 5 rehearsal items

## Judge Q&A Draft
- Question
- Safe answer

## Wording Check
- Files or sections checked
- Result
- Any lines requiring TASK-018 review

## Closeout Notes
- Whether TASK-040 definition of done is met
- Remaining Day 5 items

When finished:
- Update memory/session.md with the task context, files changed, and wording
  check result.
- Move TASK-040 to completed only if the report genuinely satisfies its
  definition of done. Otherwise leave it active and state exactly what remains.
- Do not modify memory/decisions.md, memory/known-issues.md, or
  memory/architecture.md unless the work created a real decision, issue, or
  architecture change.
- Final response should briefly name the output file, whether the wording check
  passed, and what remains for TASK-018 or Day 5.
```
