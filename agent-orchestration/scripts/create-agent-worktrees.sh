#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/repo"
  exit 1
fi

REPO="$1"
BASE="$HOME/local-ai-workstation/worktrees"
NAME="$(basename "$REPO")"

mkdir -p "$BASE"

cd "$REPO"

git status --short

git worktree add "$BASE/${NAME}-opencode" -b "agent-eval/opencode" || true
git worktree add "$BASE/${NAME}-aider" -b "agent-eval/aider" || true
git worktree add "$BASE/${NAME}-cline" -b "agent-eval/cline" || true
git worktree add "$BASE/${NAME}-openhands" -b "agent-eval/openhands" || true

echo "Created or verified agent worktrees under: $BASE"
git worktree list
