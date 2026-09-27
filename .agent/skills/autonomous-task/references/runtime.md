# Runtime and automatic continuation

Read this when starting or resuming a run. Discover live capabilities; do not infer available tools from the product name or copy a remembered API schema.

## Capability check

Establish and record:

- A real delegation facility for two dedicated workers (generator and discriminator) in addition to the coordinator, its concurrency limits, and a way to launch a fresh final discriminator context. Queue or retire finished workers when necessary; never simulate extra contexts with role labels.
- A durable workspace accessible to the current run and future scheduled runs.
- A native continuation mechanism that can invoke the agent again, including its host availability and restart behavior.
- Available status, cancellation, and scheduling tools, plus actual user-authorized resource limits.

If the required separate workers cannot be launched, state the missing requirement and preserve preparation work. Capture successful launch receipts and failed attempts; do not claim independent review without actual returned worker output. Do not pretend a single-agent review meets the contract. If only restart support is unavailable, complete as much authorized work as the active session permits, save checkpoints, and clearly report that unattended resumption is unavailable. Do not call this a fully automatic setup.

## Arm once, then work

Once the human has approved the contract including automatic continuation, arm a supported native continuation mechanism without a second routine approval. Follow tool-enforced authorization requirements.

- In Codex, discover the automation tool first. If available, use a heartbeat attached to the current task for requested automatic wakeups, following its current schema. Inspect existing automations and reuse/update the matching one instead of creating duplicates. A standalone scheduled task is appropriate only if the user requested that mode. Record the returned ID and verify the saved target, prompt, schedule, and active state using supported readback.
- Use native goal tools only when the user explicitly requested a goal and the tools are available. Follow their current preconditions and budget/status rules. Inspect any existing goal before creating one; never replace an unrelated active goal. Do not assume a native goal alone guarantees restart recovery.
- In Cursor or another host, discover its actual background-agent, scheduler, subscription, or continuation facilities and verify their documented behavior before using them. Do not invent a tool name or assume Codex's tools exist there.
- Prefer a single mechanism that provides the needed continuation. If a goal loop and a recovery heartbeat both exist, make the heartbeat check for active work and skip duplicate execution.

Choose and record a sensible wake interval for the task and host; use events for observable external changes when supported. Waiting is for a dependency or recovery, not a substitute for continuing productive work now. Back off unchanged blocked checks. Do not use a shell sleep loop, cron entry, printed sentinel, or instruction file as a claim that the model will wake unless an actual configured host integration consumes that signal.

The saved wake prompt must contain the absolute workspace and checkpoint paths, run ID, approved contract version, and instructions equivalent to:

> Resume this existing autonomous-task run from its checkpoint. If another live coordinator owns it, exit quietly. Before any task action, record any new explicit human instruction authorizing resumption or additional resources, preserving cumulative usage. A scheduled wakeup never supplies that authorization. Then check user instructions, terminal/pause/cancel state, and cumulative limits; if complete, paused, cancelled, or budget-exhausted, perform only applicable cleanup. For a blocker, check its recorded resume condition first. Read the approved contract, worker launch receipts, review phase, and unresolved challenge/response records; verify actual workspace and external state. Reconnect or relaunch distinct generator and discriminator workers with the role briefs from adversarial-review.md. Record their real returned identities and outputs. Continue substantive challenge, generation, revision, or retest without reopening settled decisions. All-PASS criteria alone cannot finish the run: require resolution of material challenges and the fresh final discriminator review. Notify only on meaningful changes, completion, failure, or required user action.

Confirm continuation is armed only after the tool succeeds and readback matches. Record a failed/unsupported setup honestly and continue useful active-session work. A local scheduler may require the app or machine to be awake; persist state for its next supported opportunity and disclose the actual limitation. Never promise execution while the host is offline without a verified remote runner.

## Prevent overlapping execution

Prefer a native guarantee that only one run can own the task. Otherwise use an atomic ownership primitive such as exclusive creation of a lock directory in the run folder, recording coordinator/task identity and a heartbeat. Refresh ownership at checkpoints. Only the owning coordinator updates the main checkpoint and authorizes deliverable changes; its assigned generator may edit the candidate within that delegation. Reviewers write only to their assigned review area.

A wakeup that finds a live owner exits quietly. After a crash, verify the recorded owner's liveness through the host or process tools before taking over. An old timestamp alone is insufficient when the owner could still be working. If liveness cannot be established, defer writes and report the recovery obstacle; do not launch competing generators. On deliberate handoff or suspension, quiesce workers and record their state before releasing ownership; never leave a generator writing after its coordinator relinquishes ownership.

## Resume without replaying side effects

Only a new explicit human instruction can release a user pause/cancel or authorize additional resources; a scheduled "resume" prompt cannot. Record that instruction, update the applicable status or allowance before the guard below, and preserve all cumulative usage. Resume only when the recorded stop conditions are actually cleared. A completed run remains complete unless the human requests new work.

1. Acquire ownership and read the contract, state, latest candidate, review, and operation journal.
2. Check user steering, terminal/pause/cancel status, and cumulative budgets immediately. If complete, paused, cancelled, or budget-exhausted, do not retry task operations or launch workers; perform only applicable cleanup. An exhausted allowance cannot be reset by a new process or heartbeat. For a blocked run, check its recorded resume condition before dependent work.
3. Inspect actual files, running workers, and external state. A checkpoint is a recovery guide, not proof that an operation finished.
4. For an authorized active run, reconcile any operation marked started but not confirmed. Query for an existing result or use an operation-specific idempotency key before retrying. An unresolved non-idempotent external action is a blocker for that action.
5. Reconnect to still-live workers; relaunch lost generator/discriminator workers in separate contexts with their role briefs, approved contract, current artifacts, and open challenges. Record actual launch receipts and returned work. Restore whether approach challenge, candidate stress test, or final review is pending. Restore the generator’s pending approach handoff/release status as well. A relaunch does not erase findings or count as a final review by itself. A fresh final review must use a new context without inherited verdicts, not merely a new prompt in the same worker. Invalidate stale reviews when relevant content or dependencies changed.
6. Continue the recorded next step, updating the checkpoint after each meaningful change.

On completion/cancel disable only this run's recorded wakeup IDs. On a hard blocker, retain only justified lightweight checks for an observable resume condition; disable pointless repeated work. Preserve terminal state if scheduler cleanup fails so the next wake is harmless.
