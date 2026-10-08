# Firstmate personal context and the My dashboard

Firstmate owns the durable context. Manual dashboard editors change those records through the shared locked/versioned store. Voice capture submits a durable request for Firstmate to interpret and apply; Firstmate does not connect to the dashboard to obtain or change its agenda.

## Ownership and normal loading

- `firstmate/data/projects.md` remains Firstmate's project registry. Its normal session-start context digest already loads this file. Registration, delivery policy and worker supervision retain their existing workflows.
- `firstmate/.pi/APPEND_SYSTEM.md` is Pi's supported, automatically loaded project-context file. Its marked personal-agenda section owns personal to-dos, reminders, unmatched personal projects, and the user's details for registered projects. Matching projects link to registry names; they are not registered twice.
- The dashboard combines these two Firstmate-owned sources into one view. Registry-only projects appear without copying registry records into the agenda. When personal details are added to one, only an annotation is saved.
- `My/data/todos.json` becomes an inactive legacy file. Only successfully migrated `projects`, `tasks` and `reminders` arrays are emptied; other keys, focus history, voice notes, and backups remain.

Pi automatically reads the agenda at the next safe reload/session start. An already-running Firstmate conversation is not rewritten or refreshed by migration. Its current work and workers must remain uninterrupted.

## Editing from either side

Use the dashboard normally, including voice input. In Firstmate, after its next safe reload, ask to manage personal projects, tasks or reminders. The local `personal_context_read` and `personal_context_update` tools access Firstmate's own files and work with the dashboard server stopped. A local read supplies a version before an edit. Once loaded, the extension also detects changed durable context at the next normal Firstmate turn and adds the fresh records automatically; unchanged records are not repeatedly injected. No dashboard fetch is involved.

All normal editors share an operating-system file lock and version checks. Keep the stable `.pi/.personal-context.lock` file. Do not hand-edit the marked agenda block while editors are active; a raw file edit bypasses the shared write contract. The rest of the append-system prompt is preserved by agenda updates. A future global `~/.pi/agent/APPEND_SYSTEM.md` needs deliberate reconciliation because Pi gives the project file precedence.

Personal task creation never dispatches a worker. Adding a personal project does not register it for worker execution. A registered project can be marked paused/done or annotated here; removing its registration still belongs to Firstmate's existing project-management workflow.

Unknown existing record fields and IDs are preserved. Changes validate fields and dates; migrated legacy reminders with no date remain intact. Firstmate uses ISO calendar dates and must resolve relative dates in the user's timezone.

## Voice, progress and failure handling

My transcribes locally and saves the exact quoted transcript in `data/.agenda-requests/`, then sends a fixed agenda-only request through Firstmate's existing `fm-inbox.sh note --request-id` owner. My does not launch an independent agenda-editing agent or archive new requests through the legacy inbox. Pending delivery survives errors and server restarts; retries keep the same identity/body. Firstmate reads current context and applies edits through `personal_context_update`, reconsidering after a version conflict. No failed or stale request restores an older snapshot over a newer edit.

Announcement or acknowledgment means pending/received, not applied. The UI shows success only from a matching durable actual outcome, and distinguishes clarification/no-change/rejection. Firstmate keeps projects long-term, deletes only confirmed completed personal tasks / one-off reminders, and clarifies ambiguous recognition or targets. Dictated software work is not execution permission; personal-context snapshots are not printed in replies. The separate music notebook route remains record-only. See [voice agenda requests](../../docs/voice-agenda.md) for reply format, recovery and the receiver's non-transactional edit-before-reply crash limitation.

Scheduled project-progress updates also use the shared versioned store. Concurrent Firstmate changes cause stale updates to fail instead of overwriting them. Corrupt or missing context fails closed; the dashboard never falls back to the old JSON.

The superseded `my_dashboard_read` / `my_dashboard_update` extension, its HTTP client and installer, and `/api/dashboard` implementation have been removed. The normal server has no legacy JSON read/write branch and requires the Firstmate context binding. The `/api/todos` compatibility URL addresses the same Firstmate store as `/api/workspace`; it is not another source. Migration/recovery tooling and historical backups remain separate from runtime operations.

## Migration and recovery

`prepare-dashboard-migration.py` creates a private, read-only preparation bundle. It reconciles project directory identities and preserves every field without changing either store.

`migrate-dashboard-context.py --my-root /path/to/My --apply` requires only the dashboard to be stopped. It refuses existing context/bindings or an unreviewed global append prompt, snapshots source and relevant destination files, checks for intervening edits, creates and verifies the Firstmate agenda, changes only the owned extension setting, binds the dashboard, then empties only the verified source arrays. It never runs Firstmate startup/supervision commands or signals its processes. Existing preferences, registry, backlog and worker state are not rewritten.

Backups and manifests are under `agent-workflow/archives/personal-context-migration-*`. To recover after a later operational change, stop the dashboard and coordinate a safe Firstmate pause first. Preserve newer agenda edits; do not blindly restore the old JSON as a second source. The migration itself rolls back its own files on a synchronous failure and retains its private backup for inspection.

## Validation

Run `python3 -m unittest discover -s tests -q` from My. Set `PI_PACKAGE_DIR` to the installed `@earendil-works/pi-coding-agent` directory to verify Pi's normal append-context loading and actual local tool execution. Set `MY_AGENDA_TEST_INBOX_ROOT` to read-only Firstmate owner sources for handoff coverage; tests copy the scripts into isolated homes rather than calling the real inbox. Tests use temporary fixtures, including durable voice requests/replies, receiver conflicts without rollback, HTTP edits, cross-process contention, source-field preservation, failed migration rollback, and legacy-store non-resurrection.

## Live migration receipt — 2026-10-04

The live My installation now uses Firstmate-owned context. All 4 original projects, 14 tasks and 5 reminders were preserved field-for-field. My and 元音 link to the existing `My` and `YuanYin_enjoy_llm` registrations. The audio-evaluation and music-visualization projects remain personal tracking records. `aligner` and `workflow-demo` are projected from the existing registry, giving the dashboard 6 projects without duplicate registration.

The old arrays were emptied only after destination and projection verification. Source data and destination/configuration snapshots are in `archives/personal-context-migration-1791097876072289000/`; its `verification.json` records the live checks. Previous code is in `archives/personal-context-code-1791097875976670000/`. Existing project registry and captain preferences remained byte-identical. Clock/focus data and unrelated dashboard files were not migrated or deleted.

At that migration, **50 tests passed**. Live verification checked Pi's standard context loading in an isolated loader, local Firstmate tool reads and no-op writes, dashboard reads and no-op writes, exact record preservation, and retirement of the old bridge. Verification changed no live record values. Voice concurrency/failure behavior at that time used temporary proposals and fixture agent responses; the historical health check confirmed that former inbox-agent path. Current voice handling uses the durable Firstmate handoff described above.

Only the idle dashboard was restarted. Firstmate's lock owner stayed unchanged, and no Firstmate startup, reload, messaging, worker-dispatch or stop command was run. **Its current session still needs a safe `/reload` or a normal next session to load the new context and tools.** Once loaded, subsequent agenda changes refresh automatically at the next normal turn; the dashboard can already read and edit the migrated records.

## Obsolete-code cleanup

The retired bridge and legacy direct-file inbox runner were removed after migration. That earlier cleanup introduced the temporary proposal path, which the current durable Firstmate handoff has now replaced. Record validation remains shared in `personal_records.py`; current voice tests exercise request identity, actual outcomes and receiver CAS/no-rollback behavior. Historical Clock data, voice archives and migration backups are preserved; current completed-task/reminder cleanup follows the confirmed-request policy above.

Historical cleanup verification: **40 retained/updated tests passed** in both the isolated worktree and deployed checkout. The removed tests covered only the retired bridge. The server source no longer references the legacy data file or retired endpoint. Live checks verified the shared API, unchanged history/data hashes, and healthy voice warmup. Cleanup backups remain under `archives/retired-bridge-cleanup-*`.
