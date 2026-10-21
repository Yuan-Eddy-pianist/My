# Codex personal-skill cleanup

The cleanup approved on 21 October 2026 disables 23 Cursor-derived personal
skills in Codex. `canvas` is retained. Other personal skills, including `teach`,
`explaination`, `explanation-style`, `no-mistakes`, `score-dsl`, and
`workspace-notes-bootstrap`, were not disabled by this cleanup. OpenAI-provided
system and plugin skills are unchanged.

The shared skill sources remain in `.agent/skills/` for Cursor and other users
of that collection. The live selection is machine-local in
`~/.codex/config.toml`. This repository stores only the skill-disable entries in
[`.agent/codex-skill-disables.toml`](../.agent/codex-skill-disables.toml), without
copying the rest of the machine's configuration.

## Restore the selection on another machine

1. Make a private backup of the existing `~/.codex/config.toml`.
2. Locate the installed skill files. The snapshot uses the current My clone at
   `/Users/eddy/Desktop/My/.agent/skills/`; adjust the paths for another location.
3. Merge the snapshot's `[[skills.config]]` entries into the existing Codex
   configuration. Update matching entries instead of duplicating them. Preserve
   all other settings; do not replace the whole configuration with this snapshot.
4. Restart Codex to refresh skill discovery. An existing chat can retain its
   original skill catalog.

The snapshot does not apply itself, and `install-skills.sh` does not apply it.
To re-enable a skill, remove its disable entry or set its `enabled` value to
`true`, then restart Codex. Keep `teach` available for explicit invocation; its
absence from a particular chat's supplied catalog is not a disable setting.

See the [official skill configuration guidance](https://learn.chatgpt.com/docs/build-skills).
