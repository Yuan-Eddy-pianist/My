#!/bin/zsh
# Point this machine's personal skills at this clone, for the harnesses you pick.
#
#   ./install-skills.sh                 # ask which ones
#   ./install-skills.sh cursor claude   # those only
#   ./install-skills.sh all             # Cursor, Claude, Codex, OpenCode
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

if [[ ! -d "$TARGET" ]]; then
  echo "missing $TARGET" >&2
  exit 1
fi

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
    echo "Which harnesses should use this clone's personal skills?"
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

link_root() {
  local link="$1"
  mkdir -p "$(dirname "$link")"

  if [[ -L "$link" ]]; then
    local current
    current="$(readlink "$link")"
    if [[ "$current" == "$TARGET" ]]; then
      echo "ok  $link -> $TARGET"
      return 0
    fi
    echo "replace symlink $link"
    echo "  was: $current"
    rm "$link"
  elif [[ -d "$link" ]]; then
    local backup="${link}.bak.$(date +%Y%m%d%H%M%S)"
    echo "backup $link -> $backup"
    mv "$link" "$backup"
  elif [[ -e "$link" ]]; then
    echo "refusing to replace unexpected file: $link" >&2
    exit 1
  fi

  ln -s "$TARGET" "$link"
  echo "link $link -> $TARGET"
}

link_each_skill() {
  local dest="$1"
  mkdir -p "$dest"

  local skill name link
  for skill in "$TARGET"/*(N/); do
    name="$(basename "$skill")"
    [[ "$name" == .* ]] && continue
    link="$dest/$name"

    if [[ -L "$link" ]]; then
      local current
      current="$(readlink "$link")"
      if [[ "$current" == "$skill" ]]; then
        echo "ok  $link -> $skill"
        continue
      fi
      echo "replace symlink $link"
      echo "  was: $current"
      rm "$link"
    elif [[ -d "$link" ]]; then
      local backup="${link}.bak.$(date +%Y%m%d%H%M%S)"
      echo "backup $link -> $backup"
      mv "$link" "$backup"
    elif [[ -e "$link" ]]; then
      echo "skip unexpected file: $link" >&2
      continue
    fi

    ln -s "$skill" "$link"
    echo "link $link -> $skill"
  done
}

install_harness() {
  case "$1" in
    cursor) link_root "$HOME/.cursor/skills" ;;
    claude) link_root "$HOME/.claude/skills" ;;
    opencode) link_root "$HOME/.config/opencode/skills" ;;
    codex)
      link_root "$HOME/.agents/skills"
      link_each_skill "$HOME/.codex/skills"
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

echo "Using $TARGET"
for harness in "${CHOSEN[@]}"; do
  echo
  echo "== $harness =="
  install_harness "$harness"
done

echo
echo "Done. uninstall: $ROOT/uninstall-skills.sh ${CHOSEN[*]}"
