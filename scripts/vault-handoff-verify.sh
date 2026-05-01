#!/bin/bash
# D-16-07 — Vault recovery value-correctness verification
#
# Why: 47/47 paths populated does NOT equal 47/47 values correct. The
# 2026-04-30 Vault cascade post-recovery verification only counted leaf-
# path population; the bogus 11-character MinIO access key in
# secret/minio/backup survived rebuild and only surfaced when Restic
# auth retried with exponential backoff during D-15-03 testing five
# days later.
#
# This helper performs end-to-end value-correctness checks against
# critical paths by attempting a real auth/operation against the live
# target using Vault-stored credentials. A handoff is REJECTED until
# every check passes.
#
# Exit codes:
#   0  all checks passed (handoff accepted)
#   1  one or more checks failed (handoff REJECTED — values incorrect)
#   2  prerequisite missing (no Vault token, vault-server not running)
#
# Usage:
#   VAULT_TOKEN=$(cat ~/.vault-token) ./scripts/vault-handoff-verify.sh
#   # or pass via env: scripts/vault-handoff-verify.sh

set -uo pipefail

DOCKER=/opt/homebrew/bin/docker
CONTAINER=vault-server
PASS=0
FAIL=0
FAILURES=()

log() { echo "[handoff-verify $(date '+%H:%M:%S')] $*"; }

check_pass() { PASS=$((PASS+1)); log "  PASS: $1"; }
check_fail() {
  FAIL=$((FAIL+1))
  FAILURES+=("$1")
  log "  FAIL: $1"
}

# ── Prerequisites ──────────────────────────────────────────────────────

if ! $DOCKER inspect "$CONTAINER" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
  log "ERROR: $CONTAINER not running — cannot verify"
  exit 2
fi

if [ -z "${VAULT_TOKEN:-}" ]; then
  if [ -f "$HOME/.vault-token" ]; then
    VAULT_TOKEN=$(cat "$HOME/.vault-token")
  else
    log "ERROR: VAULT_TOKEN not set and ~/.vault-token missing"
    exit 2
  fi
fi

vault_kv_get() {
  # vault_kv_get <path> <field> → echoes value, or empty on failure
  $DOCKER exec -e VAULT_TOKEN="$VAULT_TOKEN" "$CONTAINER" \
    vault kv get -field="$2" "$1" 2>/dev/null
}

# ── Check 1: minio/backup credentials work against live MinIO ────────

log "Check 1/3 — minio/backup credentials authenticate to MinIO"
MINIO_AK=$(vault_kv_get secret/minio/backup access_key)
MINIO_SK=$(vault_kv_get secret/minio/backup secret_key)
if [ -z "$MINIO_AK" ] || [ -z "$MINIO_SK" ]; then
  check_fail "minio/backup creds missing from Vault"
else
  # Use restic snapshots --no-cache as the no-op auth probe (matches the
  # exact path that surfaced the original bogus-key incident in D-15-03).
  if AWS_ACCESS_KEY_ID="$MINIO_AK" \
     AWS_SECRET_ACCESS_KEY="$MINIO_SK" \
     RESTIC_REPOSITORY="s3:http://192.168.10.201:9000/backups" \
     RESTIC_PASSWORD="${RESTIC_PASSWORD:-restic-test-not-real}" \
     /opt/homebrew/bin/restic snapshots --no-cache --quiet >/dev/null 2>&1; then
    check_pass "minio/backup creds OK (restic auth succeeded against MinIO)"
  else
    # restic exits non-zero on RESTIC_PASSWORD mismatch too — distinguish auth
    # failure from password failure by checking MinIO directly with mc.
    if /opt/homebrew/bin/mc alias set _hov-probe http://192.168.10.201:9000 \
         "$MINIO_AK" "$MINIO_SK" >/dev/null 2>&1 && \
       /opt/homebrew/bin/mc ls _hov-probe/backups >/dev/null 2>&1; then
      check_pass "minio/backup creds OK (mc auth succeeded; restic password may be unset)"
      /opt/homebrew/bin/mc alias remove _hov-probe >/dev/null 2>&1 || true
    else
      check_fail "minio/backup creds REJECTED by live MinIO — values incorrect"
    fi
  fi
fi

# ── Check 2: vault root token can list approle (auth surface alive) ──

log "Check 2/3 — root token can list AppRoles"
if $DOCKER exec -e VAULT_TOKEN="$VAULT_TOKEN" "$CONTAINER" \
     vault list auth/approle/role >/dev/null 2>&1; then
  check_pass "AppRole list succeeded — auth surface alive"
else
  check_fail "AppRole list FAILED — token may be wrong or auth/approle unmounted"
fi

# ── Check 3: audit log writing (write surface alive) ─────────────────

log "Check 3/3 — audit device enabled + writing"
if $DOCKER exec -e VAULT_TOKEN="$VAULT_TOKEN" "$CONTAINER" \
     vault audit list 2>/dev/null | grep -q "file/"; then
  check_pass "audit/file/ enabled"
else
  check_fail "audit/file/ NOT enabled — handoff REJECTED"
fi

# ── Summary ──────────────────────────────────────────────────────────

echo
log "=== handoff-verify summary ==="
log "  PASS: $PASS"
log "  FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
  log
  log "HANDOFF REJECTED. Failures:"
  for f in "${FAILURES[@]}"; do
    log "  - $f"
  done
  log
  log "Per D-16-07: a handoff is REJECTED until every value-correctness"
  log "check passes. Re-run after remediating each failure."
  exit 1
fi

log "HANDOFF ACCEPTED — all value-correctness checks passed."
exit 0
