#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ "${1:-}" != --configure-only ]; then
  if [ "$(uname -s)" = Darwin ]; then
    command -v brew >/dev/null 2>&1 || { echo 'Install Homebrew from https://brew.sh, then run this again.'; exit 1; }
    brew install node python bash git gh jq fd ripgrep
    brew install --cask wezterm
  else
    for tool in node npm python3 bash git gh jq curl; do
      command -v "$tool" >/dev/null 2>&1 || { echo "Install $tool using your Linux package manager, then retry."; exit 1; }
    done
  fi
  npm install -g --ignore-scripts @earendil-works/pi-coding-agent@0.87.1 @openai/codex@0.157.1 gh-axi@0.1.35 tasks-axi@0.2.6 quota-axi@0.1.55 lavish-axi@0.1.79 chrome-devtools-axi@0.1.35 chrome-devtools-mcp@1.10.1 gnhf@0.1.50
  if ! command -v herdr >/dev/null 2>&1; then sh "$ROOT/installers/herdr-install.sh"; fi
  if ! command -v treehouse >/dev/null 2>&1; then bash "$ROOT/firstmate/bin/fm-install-treehouse.sh" "$HOME/.local/bin"; fi
  if ! command -v no-mistakes >/dev/null 2>&1; then NO_MISTAKES_LINK_DIR="$HOME/.local/bin" sh "$ROOT/installers/no-mistakes-install.sh"; fi
  pi install npm:pi-web-access@0.32.0
  pi install npm:@ryan_nookpi/pi-extension-codex-fast-mode@0.2.7
fi
python3 "$ROOT/scripts/configure.py"
codex --version
pi --version
echo 'Sign in on this device: pi → /login openai-codex; gh auth login; codex login.'
echo 'Then open Start.command. Use README.md for Windows/WSL and transfer steps.'
