#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ "${1:-}" = --terminal ] || [ "${1:-}" = --headless ]; then
  exec python3 "$ROOT/scripts/start.py" "$@"
fi
if command -v wezterm >/dev/null 2>&1; then
  exec wezterm start --cwd "$ROOT/firstmate" -- "$ROOT/Start.command" --terminal
fi
exec python3 "$ROOT/scripts/start.py"
