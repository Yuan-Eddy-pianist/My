#!/bin/zsh
# Remove only this clone's links and its Codex-to-Cursor canvas bridge.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROG="${0##*/}"
TARGET="$ROOT/.agent/skills"
LEGACY_TARGET="$ROOT/.cursor/personal-skills"
source "$ROOT/skills-common.zsh"

unlink_if_ours() {
  local link="$1" expected="$2"
  if same_target "$link" "$expected"; then
    rm "$link"
    echo "removed $link"
  fi
}

unlink_root() {
  unlink_if_ours "$1" "$TARGET"
  unlink_if_ours "$1" "$LEGACY_TARGET"
}

uninstall_harness() {
  case "$1" in
    cursor) unlink_root "$SKILLS_USER_ROOT/.cursor/skills" ;;
    claude) unlink_root "$SKILLS_USER_ROOT/.claude/skills" ;;
    opencode) unlink_root "$SKILLS_USER_ROOT/.config/opencode/skills" ;;
    codex)
      unlink_root "$SKILLS_USER_ROOT/.agents/skills"
      local skill
      for skill in "$TARGET"/*(N/); do
        [[ "${skill:t}" == .* || ! -f "$skill/SKILL.md" ]] && continue
        unlink_if_ours "$SKILLS_USER_ROOT/.codex/skills/${skill:t}" "$skill"
        unlink_if_ours "$SKILLS_USER_ROOT/.codex/skills/${skill:t}" "$LEGACY_TARGET/${skill:t}"
      done
      unlink_if_ours "$SKILLS_USER_ROOT/.codex/skills/canvas" "$SKILLS_USER_ROOT/.cursor/skills-cursor/canvas"
      ;;
  esac
}

if [[ "${1:-}" == -h || "${1:-}" == --help || "${1:-}" == help ]]; then
  usage
  exit 0
fi
CHOSEN=()
choose_harnesses "Remove this clone as personal skills for which harnesses?" "$@"
for harness in "${CHOSEN[@]}"; do
  echo "== $harness =="
  uninstall_harness "$harness"
done
echo "Done."
