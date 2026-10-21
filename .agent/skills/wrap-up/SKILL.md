---
name: wrap-up
description: "Wraps up Firstmate work in at most two user-facing rounds: an inventory for decisions, then authorized execution and a durable next-day handoff. Unfinished work may remain preserved. Invoke explicitly for a day-to-day wrap-up."
disable-model-invocation: true
---

# Wrap up

Use the active Firstmate home's instructions, lifecycle skills and existing tools. Resolve paths from `FM_HOME`. This skill grants no merge, push, discard, deletion or new-work authority.

## Round 1 — inventory, not a demand to resolve everything

Check this home's relevant assignments against the original requests, saved deliverables, actual Git state and owned worker processes. Distinguish running agents, open terminal shells, retained task records and Treehouse directories.

Give one concise, concrete inventory:
- Uncommitted work: project, directory, changed-file scope and anything that cannot safely be committed, such as credentials, environments or model files.
- Unmerged work: branch/commit and a brief description of what it contains.
- Worker terminals and temporary directories: which can be closed or removed, which contain unique work, and which have a real application/service dependency.

These are facts for the user to know, not obligations to settle today. Ask once which items to commit, merge, delete, finish now, or retain for tomorrow. Do not repeatedly ask about previously deferred items. If the user's current request already gives those choices, apply them without asking again and proceed directly to the final round.

## Round 2 — execute the choices and hand off

Apply only the user's specified choices using the existing guarded paths. Commit or merge only the selected work; a commit is not a merge or push. Delete only the specified directories after the applicable preservation and ownership checks. Record the exact choices in the existing backlog/lifecycle records.

Keep everything unselected or explicitly deferred. Uncommitted and unmerged work may remain overnight: record its exact directory, branch/HEAD, changed-file scope, current result and next action so tomorrow can resume without guessing. Preserve files, reports and necessary evidence; do not create a parallel tracker or restart work merely to make the queue empty.

Separate agent shutdown, terminal closure and directory cleanup. Keeping code or a Treehouse directory does not require keeping its agent running. For the end-of-day stop, stop owned workers and close their terminals where the existing tools can preserve the selected work. Keep unrelated applications/services and this conversation running unless explicitly told otherwise. Verify agent exit, terminal absence and retained files independently; never infer one from another.

If an operation is refused or a new material ambiguity appears, preserve the affected item and report the exact blocker in the final handoff. Continue independent authorized actions. Do not force through a refusal, invent permission, build new cleanup machinery, or start a third decision round just to settle every item. A blocker can remain recorded for tomorrow; do not claim the blocked action succeeded.

Before the final handoff, fresh-read My's authoritative project records with `personal_context_read`. Match existing projects by ID and linked directory, not title alone. Use `personal_context_update` with that version to maintain each relevant project's existing `goal` / `progress`: concise evidence-backed progress, what finished, what remains uncommitted/unmerged/blocked, and the exact next-session starting point. Re-read and reconsider on conflict; verify the saved result. Preserve IDs, unknown fields, history, execution settings, unrelated projects and all tasks/reminders. Never hand-edit the marked JSON, revive the retired Git-history updater, or maintain a second editable Firstmate project list. Project registration/delivery changes still require the active home's project-management guards and its supported registry interface.

Git status and filenames are evidence of unfinished work, not proof of delivered features. Distinguish implemented, tested, committed and landed outcomes. No new Git commit does not mean no progress: retain meaningful handoff context and record evidence-backed decisions, blockers or next steps. Do not erase history or append duplicate entries just to show a daily update. This workspace is the shared before/after-work handoff, not a recurring autonomous rewrite or a request to execute deferred work. If the workspace is unavailable, preserve the handoff in existing task evidence and report the blocker; do not create another registry.

Load and follow the active home's `.agents/skills/stow/SKILL.md` after reconciliation. Let stow own memory curation and open-record persistence, including its required checks and receipt. My owns the project records; stow and the worker backlog keep their existing separate responsibilities.

Finish with one concise handoff: what was committed/merged/deleted, what workers/terminals stopped, what remains with its location and next action, and any failed or blocked operation. A successful wrap-up means the chosen actions and handoff are complete, not that every project issue or branch is resolved. Repeating wrap-up leaves already-settled work alone.
