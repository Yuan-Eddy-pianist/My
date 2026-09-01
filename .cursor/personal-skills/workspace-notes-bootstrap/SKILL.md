---
name: workspace-notes-bootstrap
description: >-
  Manual-only. Creates a template Mynote.md at the workspace project root when
  missing, and edits it only when the user explicitly requests an edit in the
  current turn. Use only when personally attached or invoked by the user.
---

# Workspace notes bootstrap (`Mynote.md`)

This skill is manual-only. Do nothing unless the user personally attaches or
invokes it in the current turn.

## Bootstrap behavior

When invoked, create `Mynote.md` at the workspace project root if it is missing.
Copy [Mynote-template.md](Mynote-template.md) and replace the placeholder under
**Canonical workspace path** with the absolute workspace-root path.

If `Mynote.md` already exists, leave it untouched unless the user explicitly
asks to edit, append, consolidate, or migrate content into it in the current
request.

## Authorization boundary

- Creating a missing `Mynote.md` from the template is authorized by invoking
  this skill.
- Any later content change requires explicit user permission in that turn.
- Scope edits to the requested material and preserve unrelated notes.
- Never delete or rename `Mynote.md` unless the user explicitly requests it.
- Do not create or maintain `updates.md`; it is not part of this workflow.

`Mynote.md` belongs at the repository or project root: the folder opened as the
workspace, normally containing `.git`, `package.json`, `pyproject.toml`, or the
project's main source directories.
