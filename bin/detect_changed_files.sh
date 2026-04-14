#!/bin/sh
set -eu

# Priority ordering for detection (Stage-3/Stage-4 literal lanes + Stage-5 dual batches):
# 1) CLI args remain the operator-provided authority for Codex-managed runs
# 2) CHANGED_FILES env (space/newline separated) stays the literal override for scripted probes, now tagging Manager-4 Stage-5 entries and noting candidate successes toward promotion readiness
# 3) git diff/ls-files fallback only seeds Stage-4/Stage-5 scans when nothing else is provided, and Stage-5 records the resulting scope in traces'

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
