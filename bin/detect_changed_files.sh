#!/bin/sh
set -eu

# Priority ordering:
# 1) CLI args: operator-provided authority for Codex-managed runs
# 2) CHANGED_FILES env: literal override for scripted probes
# 3) git diff/ls-files fallback: seeds scans when nothing else is provided

# Priority 1: CLI args
if [ "$#" -gt 0 ]; then
    for f in "$@"; do
        printf '%s\n' "$f"
    done
    exit 0
fi

# Priority 2: CHANGED_FILES env (space- or newline-separated)
if [ -n "${CHANGED_FILES:-}" ]; then
    printf '%s\n' "$CHANGED_FILES" | tr ' ' '\n' | grep -v '^[[:space:]]*$' || true
    exit 0
fi

# Priority 3: git diff/ls-files fallback
{
    git diff --name-only 2>/dev/null || true
    git ls-files --others --exclude-standard 2>/dev/null || true
} | sort -u
