<!--
Purpose:        Current session handoff only
Owner:          Currently active agent
Update Trigger: Every session
Harness Version: 1.1
-->

# Current Session — Outlook AI Signals

_Last updated: 2026-07-13_

Git history preserves earlier session states; do not create per-session archive
files.

## Session

- **Role**: PM / Planner
- **Branch**: `pm/TASK-139-agent-constitution-cleanup`
- **Goal**: Reorganize `AGENTS.md` without changing its policy boundaries.
- **Status**: Complete; TASK-021 presentation insertion and rehearsal remain.

## Completed

- Added an operational quick reference and linked contents to `AGENTS.md`.
- Replaced task-style checkboxes in permanent restrictions with semantic rule
  lists and consolidated the duplicated context-path rule.
- Removed task-specific approval history and task/ADR identifiers from the
  constitution while retaining the permanent safety constraints. Historical
  records remain in decisions, completed tasks, and task reports and cannot be
  reused as current authorization.
- Preserved the incoming TASK-021 capture work and its uncommitted artifacts.
- Started the existing local Backend and Frontend without changing environment
  files, dependencies, schema, public API, infrastructure, or deployment state.
- Captured one representative issue through Home, Detail, 7-day chart, stored
  v8 briefing, interpretation guide, and isolated scenario conversation.
- Produced `outputs/outlook-ai-signals-demo.mp4` as a 49.5-second, 1280×720,
  30fps silent H.264 video with Korean captions and 0.5-second fades.
- Added `reports/task-021-demo-video-capture.md` with the screen sequence,
  provider-use record, verification, copy check, and remaining TASK-021 work.
- Preserved the prior TASK-138 handoff: the external
  `/Users/sonmyeong-gwan/Desktop/2팀_발표_수정본.pptx` has an explicit
  technology-stack slide after team roles, shifted subsequent page markers,
  and the user-owned video placeholder.

## Verification

- Local Markdown targets resolve, heading anchors are unique, the constitution
  has no concrete task/issue/ADR identifiers outside generic branch examples,
  Prettier formatting succeeds, and `git diff --check` passes.
- Permanent restrictions and approval gates remain present; no wording/safety
  policy, runtime, API, schema, dependency, data, infrastructure, deployment,
  provider, or production state changed.
- FFprobe confirms one H.264 video stream, no audio stream, 1280×720, 30fps,
  49.5 seconds, and a 2.0 MB file with fast-start metadata.
- A six-frame contact sheet confirms the intended sequence, Korean captions,
  data timing, interpretation caution, and final validated scenario content.
- The scenario evaluation used one purpose-bound local OpenRouter call costing
  USD 0.005936 and stored three validated blocks without retry.
- The external 18-slide presentation previously passed template fidelity,
  overflow, LibreOffice rendering, ZIP integrity, technology-term presence,
  and prohibited-wording checks; it still requires video insertion.
- New caption text passed the project wording check; no deployment, production
  write, schema/dependency/API change, secret edit, or environment-file edit
  occurred.

## Next handoff

TASK-139 is complete. Continue TASK-021 by inserting
`outputs/outlook-ai-signals-demo.mp4` into the final 18-slide presentation,
verify automatic muted playback and the first frame, then rehearse the full talk
and static fallback sequence. TASK-128 and TASK-109 remain separate active work.
