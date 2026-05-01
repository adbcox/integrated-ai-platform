#!/bin/bash
# Daily Restic backup. Authenticates to Vault via AppRole.
# Schedule: launchd or cron at 02:00.
#
# Auth model:
#   - role-id and secret-id at /Users/admin/.vault-approle/backup/ (mode 600)
#   - obtains short-lived (1h TTL) Vault token via AppRole login
#   - revokes its own token on completion
#
# Required Vault state:
#   - AppRole "backup" with policy "backup" (read on secret/restic/backup, secret/minio/backup)
#   - secret/restic/backup: password, repository
#   - secret/minio/backup: access_key, secret_key
#
# Refs: H1 §2 (Foundation Hardening Block 1)

set -euo pipefail

# Ensure Homebrew binaries are on PATH for cron / minimal-PATH contexts.
# /opt/homebrew/bin = Apple Silicon; /usr/local/bin = Intel / fallback.
# Without this, restic / jq / curl resolution fails under cron's stripped
# PATH and the script either errors with "command not found" or, worse,
# misattributes the failure to a network problem.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
APPROLE_DIR="/Users/admin/.vault-approle/backup"
LOG_PREFIX="[backup $(date '+%Y-%m-%d %H:%M:%S')]"
log() { echo "$LOG_PREFIX $*"; }

if [ ! -r "$APPROLE_DIR/role-id" ] || [ ! -r "$APPROLE_DIR/secret-id" ]; then
  log "ERROR: AppRole credentials missing at $APPROLE_DIR"
  exit 1
fi

ROLE_ID=$(cat "$APPROLE_DIR/role-id")
SECRET_ID=$(cat "$APPROLE_DIR/secret-id")

LOGIN_RESP=$(curl -s -X POST \
  -d "{\"role_id\":\"$ROLE_ID\",\"secret_id\":\"$SECRET_ID\"}" \
  "$VAULT_ADDR/v1/auth/approle/login")

VAULT_TOKEN=$(echo "$LOGIN_RESP" | jq -r '.auth.client_token // empty')
if [ -z "$VAULT_TOKEN" ]; then
  log "ERROR: AppRole auth failed: $(echo "$LOGIN_RESP" | jq -r '.errors // .')"
  exit 1
fi

vault_get() {
  curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
    "$VAULT_ADDR/v1/secret/data/$1" \
    | jq -r ".data.data.$2 // empty"
}

cleanup() {
  if [ -n "${VAULT_TOKEN:-}" ]; then
    curl -s -X POST -H "X-Vault-Token: $VAULT_TOKEN" \
      "$VAULT_ADDR/v1/auth/token/revoke-self" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export RESTIC_PASSWORD
export RESTIC_REPOSITORY

AWS_ACCESS_KEY_ID=$(vault_get minio/backup access_key)
AWS_SECRET_ACCESS_KEY=$(vault_get minio/backup secret_key)
RESTIC_PASSWORD=$(vault_get restic/backup password)
RESTIC_REPOSITORY=$(vault_get restic/backup repository)

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$RESTIC_PASSWORD" ] || [ -z "$RESTIC_REPOSITORY" ]; then
  log "ERROR: required credentials missing from Vault response"
  exit 1
fi

BACKUP_DIRS=(
  "$HOME/repos/integrated-ai-platform/config"
  "$HOME/repos/integrated-ai-platform/docs"
  "$HOME/repos/integrated-ai-platform/docker/caddy"
  "$HOME/repos/integrated-ai-platform/docker/headscale"
  "$HOME/repos/integrated-ai-platform/scripts"
  "$HOME/ha-backups"
)

# D-16-04 — Vault data via warm-copy snapshot (ADR-A-017).
# The earlier raw-volume read at /var/lib/docker/volumes/vault_vault-data/_data
# never fired (root-owned in Colima; admin can't read). Replaced by a
# host-readable warm-copy at $HOME/.vault-snapshot/current produced
# fresh on every backup run. A failed snapshot is a warn-and-continue —
# repo + ha-backups must still back up.
VAULT_SNAPSHOT_DIR="$HOME/.vault-snapshot/current"
VAULT_SNAPSHOT_HELPER="$HOME/repos/integrated-ai-platform/scripts/vault-snapshot-warm.sh"
if [ -x "$VAULT_SNAPSHOT_HELPER" ]; then
  log "Producing warm-copy Vault snapshot"
  if "$VAULT_SNAPSHOT_HELPER"; then
    if [ -d "$VAULT_SNAPSHOT_DIR" ]; then
      BACKUP_DIRS+=("$VAULT_SNAPSHOT_DIR")
      log "Vault snapshot included in backup set"
    else
      log "WARN: $VAULT_SNAPSHOT_DIR missing after helper success — skipping Vault data"
    fi
  else
    log "WARN: vault-snapshot-warm.sh failed; backing up the rest of the set without Vault data"
  fi
else
  log "WARN: $VAULT_SNAPSHOT_HELPER not executable; skipping Vault data"
fi

log "Starting backup to $RESTIC_REPOSITORY"

# Initialize repo if it doesn't exist (idempotent)
if ! restic snapshots >/dev/null 2>&1; then
  log "Initializing new restic repository"
  restic init
fi

restic backup "${BACKUP_DIRS[@]}" \
  --tag daily \
  --exclude-caches \
  --verbose

log "Pruning old snapshots (keep 30 daily, 12 monthly)"
restic forget \
  --keep-daily 30 \
  --keep-monthly 12 \
  --prune

log "Backup complete"
