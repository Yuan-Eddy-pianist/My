#!/bin/zsh
# Install weekday 9:00 local-time LaunchAgent for My.
#
# macOS blocks LaunchAgents from reading Desktop/Documents/Downloads (TCC).
# The agent therefore runs schedule/launchd-runner.sh from ~/Library/... and
# hands off to Terminal.app (which already has Desktop access).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.eddy.my.weekday"
SUPPORT="${HOME}/Library/Application Support/com.eddy.my"
LOG_DIR="${HOME}/Library/Logs/com.eddy.my"
SRC_PLIST="$ROOT/schedule/${LABEL}.plist"
DEST_PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$SUPPORT" "$LOG_DIR" "$ROOT/data/tmp"
chmod +x "$ROOT/schedule/"*.sh

printf '%s\n' "$ROOT" >"$SUPPORT/root-path.txt"
cp "$ROOT/schedule/launchd-runner.sh" "$SUPPORT/launchd-runner.sh"
chmod +x "$SUPPORT/launchd-runner.sh"

if launchctl print "gui/$(id -u)/${LABEL}" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
fi

cp "$SRC_PLIST" "$DEST_PLIST"
launchctl bootstrap "gui/$(id -u)" "$DEST_PLIST"
launchctl enable "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true

echo "Installed ${LABEL}"
echo "  plist:  $DEST_PLIST"
echo "  runner: $SUPPORT/launchd-runner.sh"
echo "  root:   $ROOT"
echo "  logs:   $LOG_DIR/"
MINUTE="$(/usr/bin/plutil -extract StartCalendarInterval.0.Minute raw "$DEST_PLIST" 2>/dev/null || echo 0)"
HOUR="$(/usr/bin/plutil -extract StartCalendarInterval.0.Hour raw "$DEST_PLIST" 2>/dev/null || echo 9)"
echo "  schedule: weekdays $(printf '%02d:%02d' "$HOUR" "$MINUTE") (Mac local time)"
echo "  note: a Terminal window may flash briefly (macOS Desktop privacy)"
echo "  test now: launchctl kickstart -k gui/\$(id -u)/${LABEL}"
echo "       or: $ROOT/schedule/start-weekday.sh"
echo "  uninstall: $ROOT/schedule/uninstall-launchd.sh"
