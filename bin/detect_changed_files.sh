#!/bin/sh
set -eu

# Priority ordering for detection (Stage-3 literal lane):
# 1) CLI args remain the highest priority
# 2) CHANGED_FILES env (space or newline separated) stays second in line

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
