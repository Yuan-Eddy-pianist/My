#!/bin/zsh
# Link personal skills from this clone; application-managed skills stay in place.
# Usage: ./install-skills.sh [cursor claude codex opencode | all]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROG="${0##*/}"
TARGET="$ROOT/.agent/skills"
source "$ROOT/skills-common.zsh"

if [[ "${1:-}" == -h || "${1:-}" == --help || "${1:-}" == help ]]; then
  usage
  exit 0
fi
if [[ ! -d "$TARGET" ]]; then
  echo "missing $TARGET" >&2
  exit 1
fi

link_root() {
  local link="$1"
  mkdir -p "$(dirname "$link")"
  if same_target "$link" "$TARGET"; then
    echo "ok  $link -> $TARGET"
    return 0
  fi
  if [[ -L "$link" || -d "$link" ]]; then
    local backup="${link}.bak.$(date +%Y%m%d%H%M%S).$$"
    echo "backup $link -> $backup"
    mv "$link" "$backup"
  elif [[ -e "$link" ]]; then
    echo "refusing to replace unexpected file: $link" >&2
    exit 1
  fi
  ln -s "$TARGET" "$link"
  echo "link $link -> $TARGET"
}

link_skill() {
  local source="$1" link="$2"
  if same_target "$link" "$source"; then
    echo "ok  $link -> $source"
  elif [[ -e "$link" || -L "$link" ]]; then
    echo "leave occupied skill path: $link" >&2
  else
    mkdir -p "$(dirname "$link")"
    ln -s "$source" "$link"
    echo "link $link -> $source"
  fi
}

install_harness() {
  case "$1" in
    cursor) link_root "$SKILLS_USER_ROOT/.cursor/skills" ;;
    claude) link_root "$SKILLS_USER_ROOT/.claude/skills" ;;
    opencode) link_root "$SKILLS_USER_ROOT/.config/opencode/skills" ;;
    codex)
      link_root "$SKILLS_USER_ROOT/.agents/skills"
      local skill
      for skill in "$TARGET"/*(N/); do
        [[ "${skill:t}" == .* || ! -f "$skill/SKILL.md" ]] && continue
        link_skill "$skill" "$SKILLS_USER_ROOT/.codex/skills/${skill:t}"
      done
      local canvas="$SKILLS_USER_ROOT/.cursor/skills-cursor/canvas"
      if [[ -f "$canvas/SKILL.md" ]]; then
        link_skill "$canvas" "$SKILLS_USER_ROOT/.codex/skills/canvas"
      else
        echo "Canvas not linked: Cursor's managed canvas is not installed at $canvas" >&2
      fi
      ;;
  esac
}

CHOSEN=()
choose_harnesses "Which harnesses should use this clone's personal skills?" "$@"
for harness in "${CHOSEN[@]}"; do
  echo "== $harness =="
  install_harness "$harness"
done

echo "Done. uninstall: $ROOT/uninstall-skills.sh ${CHOSEN[*]}"
