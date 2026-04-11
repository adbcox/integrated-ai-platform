#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ".venv/bin/activate" ]; then
  echo ".venv not found; run ./bootstrap.sh first"
  exit 1
fi

source .venv/bin/activate
PORT="${PORT:-8010}"
uvicorn api_server:app --host 0.0.0.0 --port "$PORT"
