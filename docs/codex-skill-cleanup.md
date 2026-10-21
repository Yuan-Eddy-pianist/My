# Codex skill cleanup: superseded snapshot

The initial 21 October 2026 cleanup used 23 machine-local disable entries.
The approved personal-skill layout now replaces those temporary settings:
24 copied Cursor packages have been archived locally, personal skills are
centralized in My, and Codex links directly to Cursor's managed canvas.

The obsolete disable snapshot has been removed from the current tree. Its
historical version remains in Git; do not merge those path-based disables into
a new configuration. Follow [the current personal-skill layout and installation
instructions](personal-skills-layout.md) instead.

Original configuration backups and the copied-package archive stay private on
the machine where the migration ran. Application-managed skill files and
unrelated Codex settings are preserved.
