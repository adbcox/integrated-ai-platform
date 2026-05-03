#!/usr/bin/env bash
# Platform Service Registry refresh entrypoint.
# Per Service Registry MVP spec §6 — runs every 15 minutes via launchd.
#
# Output: ~/.platform-registry/{inventory.json,by-service/*.json,last-refresh.json}
# Logs:   ~/.platform-registry/refresh.log (rotated at 5MiB by launchd policy)

set -euo pipefail

REPO="${PLATFORM_REGISTRY_REPO:-/Users/admin/repos/integrated-ai-platform}"
SCRIPT="$REPO/scripts/platform-registry/lib/registry_writer.py"
OUT="${PLATFORM_REGISTRY_OUT:-$HOME/.platform-registry}"
LOG="$OUT/refresh.log"

mkdir -p "$OUT"

# Rotate log if >5 MiB
if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt 5242880 ]; then
    mv "$LOG" "${LOG}.1"
fi

ts() { date +"%Y-%m-%dT%H:%M:%S"; }

echo "[$(ts)] refresh start" >> "$LOG"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[$(ts)] ERROR: python3 not on PATH" >> "$LOG"
    exit 2
fi

if ! [ -f "$SCRIPT" ]; then
    echo "[$(ts)] ERROR: $SCRIPT missing" >> "$LOG"
    exit 3
fi

# Run with a 60-second cap; 30-second internal target per spec §10
if /usr/bin/env python3 "$SCRIPT" "$OUT" >> "$LOG" 2>&1; then
    echo "[$(ts)] refresh ok" >> "$LOG"
else
    rc=$?
    echo "[$(ts)] ERROR: refresh exit=$rc" >> "$LOG"
    exit $rc
fi

# D-17-37 — chain artifact-axis refresh so launchd run keeps both indices fresh.
# Failure here is a warning, not fatal: artifact axis is sibling, not blocker.
ARTIFACT_REFRESH="$REPO/scripts/platform-registry/refresh-artifacts.sh"
if [ -x "$ARTIFACT_REFRESH" ]; then
    if "$ARTIFACT_REFRESH" 2>>"$LOG"; then
        echo "[$(ts)] artifact refresh ok" >> "$LOG"
    else
        echo "[$(ts)] WARN: artifact refresh exit non-zero (non-fatal)" >> "$LOG"
    fi
fi
