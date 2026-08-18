#!/bin/zsh
# Runs outside Desktop (copied to ~/Library/Application Support/com.eddy.my/).
# Hands off to Terminal.app so macOS Desktop TCC does not block start.sh.
set -euo pipefail

SUPPORT="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cat "$SUPPORT/root-path.txt")"
START="$ROOT/schedule/start-weekday.sh"
LOG_DIR="${HOME}/Library/Logs/com.eddy.my"
LOG="$LOG_DIR/terminal-launch.log"

mkdir -p "$LOG_DIR"
print -r -- "=== $(date) launching via Terminal ===" >>"$LOG"

/usr/bin/osascript - "$ROOT" "$START" "$LOG" <<'APPLESCRIPT'
on run argv
  set rootPath to item 1 of argv
  set startPath to item 2 of argv
  set logPath to item 3 of argv
  tell application "Terminal"
    do script "export MY_ROOT=" & quoted form of rootPath & "; " & quoted form of startPath & " >>" & quoted form of logPath & " 2>&1; exit"
  end tell
end run
APPLESCRIPT
