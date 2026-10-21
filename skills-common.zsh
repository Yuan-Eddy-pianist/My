# Shared argument selection for install-skills.sh and uninstall-skills.sh.
SKILLS_USER_ROOT="${MY_SKILLS_HOME:-$HOME}"

# Compare symlinks without replacing application-owned directories.
same_target() {
  local link="$1" expected="$2"
  [[ -L "$link" ]] || return 1
  [[ "$(readlink "$link")" == "$expected" || "${link:A}" == "${expected:A}" ]]
}

ALL_HARNESSES=(cursor claude codex opencode)

usage() {
  cat <<EOF
Usage: $PROG [harness ...]

  1  cursor     ~/.cursor/skills
  2  claude     ~/.claude/skills
  3  codex      ~/.agents/skills, personal aliases, and a link to Cursor canvas
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
  local prompt="$1"
  shift
  local raw=("$@")
  if (( ${#raw} == 0 )); then
    if [[ ! -t 0 ]]; then
      usage >&2
      exit 1
    fi
    echo "$prompt"
    usage
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
