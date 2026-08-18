#!/bin/zsh
# Stop this clone from being the personal-skills path for the harnesses you pick.
# Only removes symlinks that still point at this repo.
#
#   ./uninstall-skills.sh                 # ask which ones
#   ./uninstall-skills.sh cursor claude   # those only
#   ./uninstall-skills.sh all
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROG="${0##*/}"
TARGET="$ROOT/.cursor/personal-skills"
ALL_HARNESSES=(cursor claude codex opencode)

usage() {
  cat <<EOF
Usage: $PROG [harness ...]

  1  cursor     ~/.cursor/skills
  2  claude     ~/.claude/skills
  3  codex      ~/.agents/skills  and  ~/.codex/skills/<skill>
  4  opencode   ~/.config/opencode/skills
  a  all

Examples:
  $PROG
  $PROG cursor
  $PROG 1 3
  $PROG all
EOF
}

normalize() {
  case "$1" in
    1|cursor) print -r -- cursor ;;
    2|claude|claude-code) print -r -- claude ;;
    3|codex|agents) print -r -- codex ;;
    4|opencode) print -r -- opencode ;;
    a|all) print -r -- all ;;
    *)
      echo "unknown harness: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
}

choose_harnesses() {
  local raw=("$@")
  if (( ${#raw} == 0 )); then
    if [[ ! -t 0 ]]; then
      usage >&2
      exit 1
    fi
    echo "Remove this clone as personal skills for which harnesses?"
    echo
    echo "  1) Cursor     ~/.cursor/skills"
    echo "  2) Claude     ~/.claude/skills"
    echo "  3) Codex      ~/.agents/skills  and  ~/.codex/skills/<skill>"
    echo "  4) OpenCode   ~/.config/opencode/skills"
    echo "  a) all"
    echo
    echo -n "Enter numbers, names, or a (e.g. 1 3 or cursor claude): "
    local line
    read -r line
    raw=(${=line})
    if (( ${#raw} == 0 )); then
      echo "nothing selected" >&2
      exit 1
    fi
  fi

  local item mapped chosen=()
  for item in "${raw[@]}"; do
    mapped="$(normalize "$item")"
    if [[ "$mapped" == all ]]; then
      CHOSEN=("${ALL_HARNESSES[@]}")
      return
    fi
    chosen+=("$mapped")
  done
  CHOSEN=("${(u)chosen[@]}")
}

unlink_if_ours() {
  local link="$1"
  local expected="$2"

  if [[ ! -L "$link" ]]; then
    return 0
  fi
  local current
  current="$(readlink "$link")"
  if [[ "$current" != "$expected" ]]; then
    echo "leave $link (points at $current)"
    return 0
  fi
  rm "$link"
  echo "removed $link"
}

uninstall_harness() {
  case "$1" in
    cursor) unlink_if_ours "$HOME/.cursor/skills" "$TARGET" ;;
    claude) unlink_if_ours "$HOME/.claude/skills" "$TARGET" ;;
    opencode) unlink_if_ours "$HOME/.config/opencode/skills" "$TARGET" ;;
    codex)
      unlink_if_ours "$HOME/.agents/skills" "$TARGET"
      if [[ -d "$HOME/.codex/skills" ]]; then
        local skill
        for skill in "$TARGET"/*(N/); do
          unlink_if_ours "$HOME/.codex/skills/$(basename "$skill")" "$skill"
        done
      fi
      ;;
  esac
}

# Older installer created this; drop it if it still points here.
if [[ -L "$HOME/.gemini/skills" && "$(readlink "$HOME/.gemini/skills")" == "$TARGET" ]]; then
  rm "$HOME/.gemini/skills"
  echo "removed leftover $HOME/.gemini/skills"
fi

if [[ "${1:-}" == -h || "${1:-}" == --help || "${1:-}" == help ]]; then
  usage
  exit 0
fi

CHOSEN=()
choose_harnesses "$@"

for harness in "${CHOSEN[@]}"; do
  echo "== $harness =="
  uninstall_harness "$harness"
done

echo "Done."
