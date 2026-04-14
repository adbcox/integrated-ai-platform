#!/bin/sh
set -eu

# Priority ordering for detection (Stage-3/Stage-4 literal lanes + Stage-5 batches):
# 1) CLI args remain the operator-provided authority
# 2) CHANGED_FILES env (space/newline separated) remains the literal default override
# 3) git diff/ls-files fallback limits Stage-4/Stage-5 scan budgets' only. Use apply_patch and do not touch any other text.

if [ "$#" -gt 0 ]; then
  for item in "$@"; do
    printf '%s\n' "$item"
  done
  exit 0
fi

if [ -n "${CHANGED_FILES:-}" ]; then
  # Supports either space-separated or newline-separated CHANGED_FILES values.
  printf '%s\n' "$CHANGED_FILES" | tr ' ' '\n' | sed '/^$/d'
  exit 0
fi

if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  (
    git diff --name-only --diff-filter=ACMRTUXB HEAD -- 2>/dev/null || true
    git ls-files --others --exclude-standard 2>/dev/null || true
  ) | sed '/^$/d' | sort -u
  exit 0
fi

exit 0
