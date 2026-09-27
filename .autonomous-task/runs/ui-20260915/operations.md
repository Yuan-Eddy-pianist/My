# Run operations

## Recovery heartbeat — confirmed

- Intention: approved contract v1 specifies a current-task recovery check every 15 minutes, with cleanup on completion or pause.
- Authorization: user “cool, start the implementation.” after contract presentation.
- Action: create native heartbeat `finish-my-ui-improvement` targeting task `01a0a2e0-ee9b-7fd1-a87b-4b99bfd49e35`.
- Outcome: create succeeded, ACTIVE; native view succeeded; saved automation.toml verified name, full recovery prompt, target task, active state, and 15-minute interval.
- Duplicate prevention: no automations folder existed before creation; current coordinator holds run/owner.lock. Wake prompt checks live ownership and terminal state.
- Cleanup complete: final R1–R5 PASS persisted; native update set this heartbeat PAUSED, and saved status/target were verified.

## Isolated preview — confirmed

- Scope: local HTTP preview on 127.0.0.1:8875. Sample workspace file is run/preview-data/todos.json, resettable from run/fixture.json. The preview wraps the existing persistence handler, limits served routes, and simulates microphone streams and processing states.
- Initial launch: workspace sandbox prevented binding a port. The approved local-preview command was retried with sandbox escalation and succeeded (process session 30125).
- Original user app at port8765 and its running timer were not manipulated.

## Disposable record browser checks — reviewer

- Reviewer initially received automatic-review rejection of a mixed reopen/delete/check batch, citing insufficient authorization.
- Reviewer checked the preview origin, source routing to disposable data, and recoverable fixture backup, then retried a single authorized sample deletion.
- Retry succeeded; reviewer reported no remaining approval blocker. No real user record was deleted.

## User-directed adjustment — 2026-09-15T03:40:51.059335+00:00

- Direct user steering approved contract v2: remove decorative copy, center dial, keep exact voice hint, display real workspace.
- Re-armed existing heartbeat with v2 prompt and verified target/status; no duplicate automation created.
- Real data was never changed: original baseline hash still matches. Prior port8875 view used isolated sample data; delivery tab now points to real port8765.
- Retired isolated preview session30125 with interrupt; exit130 confirmed and port8875 closure verified. Real server was not stopped.
- Independent round03 review returned R1–R5 PASS on final manifest, with no code/layout defect. Candidate and original data/backend hashes reverified after review.
- Persisted terminal complete state and final manifest; recovery cleanup pending.
- Cleanup complete: heartbeat PAUSED through native update, saved status and target verified. Owner record archived and owner lock released.

## September17 simplification, round04
- Contractv3 follows explicit user request; same90-minute cumulative budget (prior75). Reused heartbeat, ACTIVE status/v3 prompt verified.
- Fresh personal-data hash recorded; no data writes. Changed todos.html and styles.css only; stable round04 manifest frozen for independent review.
- Removed duplicated text and timer card chrome; focus/rest now share root palette. Syntax and source consistency checks pass.
- Final independent round04 R1–R5 PASS persisted; candidate and fresh data hashes reverified. Heartbeat PAUSED and saved status/target verified; owner released.
