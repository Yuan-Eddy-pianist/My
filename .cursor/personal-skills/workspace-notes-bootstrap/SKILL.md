---
name: workspace-notes-bootstrap
description: >-
  Manual-only. Creates template updates.md at the workspace project root when
  it is missing. Do NOT trigger automatically and do NOT apply at the start of
  a conversation. Use ONLY when the user personally attaches this skill (e.g.
  types /workspace-notes-bootstrap).
---

# Workspace notes bootstrap (updates.md)

**This skill is manual-only.** Do nothing unless the user has personally
attached/invoked it this turn. There is no automatic conversation-start check,
and no "verify before substantive work" step.

## What it does

When invoked, create `updates.md` at the workspace project root if it is
missing. If it already exists, do nothing.

| File | Source template |
|------|-----------------|
| `updates.md` | Copy [updates-template.md](updates-template.md) from this skill folder. Replace the placeholder under **Canonical workspace path** with the absolute path to the workspace root. |

**Location:** the repository / project root (the folder the user opened as the
workspace, or the root that contains `.git`, `package.json`, `tools/`, etc.).

## Rules

- Only create the file; do not overwrite or rewrite content that already exists.
- If `updates.md` already exists, leave it untouched.
- Never delete or rename `updates.md`.
- Do not append session notes, quick facts, or follow-ups — this skill only
  scaffolds the template. Ongoing edits are out of scope.
- Do not create or modify `Mynote.md` — the user maintains that file by hand.
