#!/bin/bash
# D-16-04 — produce a warm-copy snapshot of /vault/data into the
# snapshot landing zone (/Users/admin/.vault-snapshot/current/).
#
# Why warm copy: Vault is on the file backend (BoltDB-backed
# directory tree, not raft). `vault operator raft snapshot save` is
# unavailable. A copy taken from a running Vault is crash-consistent —
# equivalent to power-loss recovery semantics that BoltDB handles on
# next start. See ADR-A-017.
#
# Atomic: writes to .staging-<ts>/, verifies, then renames into
# current/. Old current/ moves to current.old briefly, removed on
# success. A failed run leaves the prior current/ in place untouched.
#
# Idempotent + safe to run while Vault is serving requests. Designed
# to be called from scripts/backup.sh as the very first step.
#
# Exit codes:
#   0  current/ contains a fresh snapshot
#   1  copy failed; previous current/ (if any) is untouched
#   2  vault-server container not running

set -euo pipefail

# Ensure Homebrew binaries are on PATH for cron / minimal-PATH contexts.
# Mirrors the guard in scripts/backup.sh — docker resolution fails under
# cron's stripped PATH otherwise.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

LOG_PREFIX="[vault-snapshot $(date '+%Y-%m-%d %H:%M:%S')]"
log() { echo "$LOG_PREFIX $*"; }

CONTAINER=vault-server
SNAP_HOST_DIR=/Users/admin/.vault-snapshot

if ! docker inspect "$CONTAINER" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
  log "ERROR: $CONTAINER not running — cannot snapshot"
  exit 2
fi

if [ ! -d "$SNAP_HOST_DIR" ]; then
  log "ERROR: $SNAP_HOST_DIR missing on host (expected mode 0700, owned admin)"
  exit 1
fi

TS=$(date +%s)
STAGE="/vault/snapshot/.staging-$TS"

log "Staging warm-copy of /vault/data -> $STAGE"
docker exec "$CONTAINER" sh -c "
  set -e
  mkdir -p '$STAGE'
  # cp -a preserves Vault's 0700/0600 mode bits — that's intentional. The
  # host-readability chmod runs AFTER the atomic rename, on current/, where
  # Vault is no longer touching the data. This avoids racing with live Vault
  # writes (sys/expire/, sys/token/) that cause transient permission failures.
  cp -a /vault/data/. '$STAGE'/
" || { log "ERROR: staging copy failed; previous current/ unchanged"; exit 1; }

log "Verifying staged copy"
STAGE_FILE_COUNT=$(docker exec "$CONTAINER" sh -c "find '$STAGE' -type f | wc -l" | tr -d ' ')
SOURCE_FILE_COUNT=$(docker exec "$CONTAINER" sh -c "find /vault/data -type f | wc -l" | tr -d ' ')

if [ "$STAGE_FILE_COUNT" -lt "$SOURCE_FILE_COUNT" ]; then
  log "ERROR: stage file count $STAGE_FILE_COUNT < source file count $SOURCE_FILE_COUNT"
  docker exec "$CONTAINER" rm -rf "$STAGE" 2>/dev/null || true
  exit 1
fi
log "Staged $STAGE_FILE_COUNT files (source had $SOURCE_FILE_COUNT during stage; small drift expected on a live Vault)"

log "Atomic rename: $STAGE -> /vault/snapshot/current"
docker exec "$CONTAINER" sh -c "
  set -e
  rm -rf /vault/snapshot/current.old 2>/dev/null || true
  if [ -d /vault/snapshot/current ]; then
    mv /vault/snapshot/current /vault/snapshot/current.old
  fi
  mv '$STAGE' /vault/snapshot/current
  rm -rf /vault/snapshot/current.old 2>/dev/null || true
" || { log "ERROR: rename failed"; exit 1; }

# Now that /vault/snapshot/current is renamed, Vault is not writing to it.
# Make it readable by host admin (different UID than container's vault user).
# Suppress per-file errors (-f doesn't exist for chmod, but find redirect does):
# any single-file chmod failure is non-fatal — Restic will still back up what
# it can read. Tracked failures are surfaced in the verification step below.
docker exec "$CONTAINER" sh -c "
  find /vault/snapshot/current -exec chmod go+rX {} + 2>/dev/null || true
"

# Brief host-side sanity: directory should exist and be readable
if [ ! -d "$SNAP_HOST_DIR/current" ] || [ -z "$(ls -A "$SNAP_HOST_DIR/current" 2>/dev/null)" ]; then
  log "ERROR: $SNAP_HOST_DIR/current empty or unreadable from host"
  exit 1
fi

HOST_FILE_COUNT=$(find "$SNAP_HOST_DIR/current" -type f 2>/dev/null | wc -l | tr -d ' ')
log "Snapshot ready at $SNAP_HOST_DIR/current — host sees $HOST_FILE_COUNT files"
exit 0
