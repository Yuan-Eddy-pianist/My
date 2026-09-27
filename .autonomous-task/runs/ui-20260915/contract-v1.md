# My UI improvement — contract v1 (approved)

## Objective and agreement

Improve the local My app for Eddy's everyday focus and task management.
Scope and general direction approved by the user's message “yes, agreed.” following the proposal to improve both 专注 and 工作台 with a clearer timer, stronger task hierarchy, and consistent styling.
Approved by the user: “cool, start the implementation.” Approval and active-work start: 2026-09-15T02:36:04.675864+00:00. Contract v1 is frozen.

Deliverables: updated app/index.html, app/todos.html, app/styles.css, and UI-related portions of app/app.js as necessary; a local preview; browser evidence and independent review under this run directory.
Style: warm off-white surfaces, restrained forest-green accents, readable Chinese typography, generous but purposeful spacing, clear section headings, minimal ornament. Keep the 35/5 focus rhythm.

## Required criteria

- R1 — Clear focus timer: large numeric remaining time and a visible 专注/休息 label; clearly differentiated primary start/pause control, reset, and skip. Evidence: desktop/mobile screenshots and a browser exercise of start, pause, reset, skip, and navigation persistence.
- R2 — Clear workspace hierarchy: short-term tasks, reminders, and long-term projects have distinct headings and useful counts; due/overdue items are readable; long paths and progress notes do not overwhelm primary titles; adding projects and viewing completed items remain easy to find. Evidence: populated, empty, and long-content browser screenshots; independent visual rubric check for hierarchy, legibility, and consistent spacing.
- R3 — Consistent, usable layout: both pages share navigation, typography, surfaces, controls, and spacing; no overlap, clipped controls, or horizontal page scrolling at 1440×900 and 390×844; keyboard focus remains visible and primary controls have accessible names. Evidence: screenshots, keyboard exercise, and DOM overflow checks at these sizes.
- R4 — Preserve core workflows: timer state survives page navigation; project add/path validation/status controls, task/reminder completion and completed-item deletion, refresh, and voice controls still operate. Evidence: browser checks against isolated sample data, including simulated voice permission/error/processing feedback. Real microphone transcription and model quality are outside UI acceptance.
- R5 — Verified, contained change: independent discriminator verifies R1–R4 on the final hashed candidate; existing persistence tests pass; pre-existing user work and personal workspace data are preserved. Evidence: candidate hashes, recorded browser/test results, baseline-to-final diff, and review verdicts.

Evaluator: a separate native subagent, read-only for deliverable files and allowed to write only its review evidence. All required criteria must PASS on the final identifiable candidate. No final human judgment is reserved.

## Scope and allowed actions

Local UI edits, isolated sample-data previews, browser checks, existing test execution, and independent subagent reviews are authorized by the approved run. The coordinator is the generator. Review occurs on a stable candidate with generator edits paused.
Do not expand into backend redesign, the standalone autonomous-task guide, cloud publishing, Git push/merge, purchases, or real personal-data test mutations.
Optional improvements: subtle transitions and helpful empty-state copy, only where they support the required criteria.

## Limits and continuation

Up to 90 minutes of cumulative active work after contract approval, including independent reviews; pause with a checkpoint if the allowance expires. Track wall-clock intervals conservatively across resumes. No purchased services or paid external API calls. Host account/tool limits still apply; exact token and monetary accounting is unavailable.
Use the native current-task heartbeat every 15 minutes for recovery, verify saved target/schedule/status, and disable it at completion or pause. Local recovery requires the host to be available; do not claim offline execution. If scheduling is unavailable, continue active-session work and report that limitation.
Each wake reads this contract and state.md, verifies owner liveness, respects the cumulative allowance and terminal states, and never launches an overlapping generator. Notify only for a meaningful change, completion, failure, or necessary user decision.

## Source material

Current app files and README, preserving pre-existing uncommitted changes; autonomous-task SKILL.md, checkpoint.md, and runtime.md already read during preparation.
