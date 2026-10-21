# Personal skills and application-managed skills

My is the source of truth for personally selected skills. Application-supplied
skills remain in the application's managed directories and are updated there.
Do not copy them into `.agent/skills/`.

## Sources and links

- `.agent/skills/`: canonical personal skill source in this repository.
- `.agents/skills`: repository discovery link to the personal collection.
- `.cursor/personal-skills`: compatibility link to the same personal collection.
- `~/.agents/skills`: Codex's user discovery link to this clone.
- `~/.codex/skills/<personal-name>`: compatibility aliases to personal skills.
- `~/.cursor/skills`: Cursor's personal discovery link to this clone.
- `~/.cursor/skills-cursor/`: Cursor's installed, managed skill collection.
- `~/.codex/skills/.system/` and Codex's plugin installation/cache locations:
  OpenAI-managed resources, left in place.
- `~/.codex/skills/canvas`: a link to `~/.cursor/skills-cursor/canvas`.

`canvas` is intentionally available to Codex through that last link. Its source
and SDK stay in Cursor's managed installation. If Cursor's canvas is not
installed, the installer reports that the bridge was skipped; it does not
copy, download or create a replacement. If a destination is already occupied
by an unrelated skill, the installer preserves it and reports the conflict.

Personal means selected or maintained by the owner; it does not mean every
skill was authored by the owner. The retained collection includes third-party
additions and explicit-invocation helpers:

- autonomous-task
- codebase-design
- domain-modeling
- excalidraw-diagram
- explaination
- explanation-style
- grill-me
- grilling
- improve-codebase-architecture
- no-mistakes
- score-dsl
- teach
- workspace-notes-bootstrap
- wrap-up

`teach` remains available for explicit tutorial requests. Its metadata disables
implicit invocation; no cleanup setting disables it.

## Install and remove links

Run `./install-skills.sh cursor codex` for those two applications, or select
other supported harnesses. The source is always `.agent/skills/`. An existing
personal root directory or different root link is backed up before that root
is repointed. Existing conflicting individual skills and application-managed
sources are preserved.

`./uninstall-skills.sh cursor codex` removes only this clone's owned links and
the managed-canvas bridge. It preserves the underlying personal and managed
skill files. Legacy links through `.cursor/personal-skills` remain recognized.

For isolated installer checks, `MY_SKILLS_HOME` can select a temporary user
root. Normal installation uses the actual user home without that override.
Run the focused regression suite with:

```bash
python3 -m unittest discover -s tests -p 'test_skill_installers.py' -v
```

## Migration from the copied collection

The approved 21 October 2026 migration archives 24 copied/adapted Cursor skill
directories outside skill-discovery roots, including the old copied canvas.
It moves four personal additions from `~/.codex/skills/` into My and leaves
compatibility links at their previous paths. Ignored local environments remain
local and are not versioned.

The machine-local archive contains the previous Codex configuration and a
manifest with source checksums and verification results. The 23 temporary
Codex disable entries pointing to the removed copies are no longer needed and
are removed; all other configuration is preserved. No complete machine
configuration or local archive belongs in Git.

This source separation supersedes the earlier `codex-skill-disables.toml`
snapshot. Do not restore those obsolete path-based disables. On a new machine,
install the personal links and let each application manage its own supplied
skills.
