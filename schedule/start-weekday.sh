#!/bin/zsh
# Weekday morning launcher: ensure My is running, then open the workspace.
set -euo pipefail

if [[ -n "${MY_ROOT:-}" ]]; then
  ROOT="$MY_ROOT"
else
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

HOST="127.0.0.1"
PORT="8765"
URL="http://${HOST}:${PORT}/app/todos.html"
LOG_DIR="$ROOT/data/tmp"
LOG="$LOG_DIR/serve.log"
PID_FILE="$LOG_DIR/serve.pid"

mkdir -p "$LOG_DIR"

is_up() {
  /usr/bin/curl -fsS --max-time 2 "http://${HOST}:${PORT}/api/health" >/dev/null 2>&1
}

start_server() {
  cd "$ROOT"
  export MY_WHISPER_BACKEND="${MY_WHISPER_BACKEND:-mlx}"
  export MY_WHISPER_MODEL="${MY_WHISPER_MODEL:-mlx-community/whisper-medium-mlx}"
  /usr/bin/nohup "$ROOT/start.sh" >>"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
}

if ! is_up; then
  start_server
  for _ in {1..60}; do
    if is_up; then
      break
    fi
    sleep 0.5
  done
fi

if is_up; then
  /usr/bin/open "$URL"
else
  echo "My failed to start. See $LOG" >&2
  exit 1
fi
