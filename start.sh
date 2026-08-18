#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install -r requirements.txt
fi
# Default: MLX medium on Apple Silicon Metal.
# Fallback override: MY_WHISPER_BACKEND=faster MY_WHISPER_MODEL=medium ./start.sh
export MY_WHISPER_BACKEND="${MY_WHISPER_BACKEND:-mlx}"
export MY_WHISPER_MODEL="${MY_WHISPER_MODEL:-mlx-community/whisper-medium-mlx}"
exec .venv/bin/python -u serve.py
