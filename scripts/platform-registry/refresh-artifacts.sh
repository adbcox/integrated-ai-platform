#!/usr/bin/env bash
# Artifact-axis registry refresh entrypoint (D-17-37 sibling to refresh.sh).
#
# Output: ~/.platform-registry/{artifacts.json,artifacts/<deliverable>.json,artifacts-last-refresh.json}
# Logs:   ~/.platform-registry/refresh-artifacts.log

set -euo pipefail

REPO="${PLATFORM_REGISTRY_REPO:-/Users/admin/repos/integrated-ai-platform}"
SCRIPT="$REPO/scripts/platform-registry/lib/artifact_writer.py"
OUT="${PLATFORM_REGISTRY_OUT:-$HOME/.platform-registry}"
LOG="$OUT/refresh-artifacts.log"

mkdir -p "$OUT"

if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv "$LOG" "${LOG}.1"
fi

ts() { date +"%Y-%m-%dT%H:%M:%S"; }

echo "[$(ts)] artifact refresh start" >> "$LOG"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[$(ts)] ERROR: python3 not on PATH" >> "$LOG"
    exit 2
fi

if ! [ -f "$SCRIPT" ]; then
    echo "[$(ts)] ERROR: $SCRIPT missing" >> "$LOG"
    exit 3
fi

if /usr/bin/env python3 "$SCRIPT" "$OUT" >> "$LOG" 2>&1; then
    echo "[$(ts)] artifact refresh ok" >> "$LOG"
else
    rc=$?
    echo "[$(ts)] ERROR: artifact refresh exit=$rc" >> "$LOG"
    exit $rc
fi
