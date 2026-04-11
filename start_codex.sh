#!/bin/sh
set -e

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -n "${PROJECT_DIR:-}" ]; then
  TARGET_DIR="$PROJECT_DIR"
elif [ -d "/app" ]; then
  TARGET_DIR="/app"
else
  TARGET_DIR="$SCRIPT_DIR"
fi

cd "$TARGET_DIR"

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "ERROR: nvm not found at $NVM_DIR/nvm.sh"
  exit 1
fi

set +u 2>/dev/null || true
. "$NVM_DIR/nvm.sh"

nvm use 22 >/dev/null 2>&1 || nvm install 22 >/dev/null 2>&1
nvm alias default 22 >/dev/null 2>&1 || true

echo "pwd: $(pwd)"
echo "user: $(whoami)"
echo "node: $(node -v)"
echo "codex: $(command -v codex || echo not-found)"

exec codex "$@"
