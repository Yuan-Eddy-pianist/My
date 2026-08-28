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

# Local LLM for my-agent (mlx-lm OpenAI-compatible server).
LLM_PORT="${MY_LLM_PORT:-8800}"
LLM_MODEL_DIR="${MY_LLM_MODEL_DIR:-models/Qwen3-30B-A3B-Instruct-2507-4bit}"
if [[ -d "$LLM_MODEL_DIR" ]] && ! /usr/bin/curl -fsS --max-time 2 "http://127.0.0.1:${LLM_PORT}/v1/models" >/dev/null 2>&1; then
  mkdir -p data/tmp
  /usr/bin/nohup .venv/bin/mlx_lm.server --model "$LLM_MODEL_DIR" --host 127.0.0.1 --port "$LLM_PORT" >> data/tmp/llm.log 2>&1 &
  echo "Started local LLM on 127.0.0.1:${LLM_PORT} (log: data/tmp/llm.log)"
fi

exec .venv/bin/python -u serve.py
