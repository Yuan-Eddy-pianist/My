#!/bin/zsh
# Remove the weekday LaunchAgent for My.
set -euo pipefail

LABEL="com.eddy.my.weekday"
DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"
SUPPORT="${HOME}/Library/Application Support/com.eddy.my"

if launchctl print "gui/$(id -u)/${LABEL}" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
fi
rm -f "$DEST"
rm -f "$SUPPORT/launchd-runner.sh" "$SUPPORT/start-weekday.sh" "$SUPPORT/root-path.txt"
rmdir "$SUPPORT" 2>/dev/null || true
echo "Removed ${LABEL}"
