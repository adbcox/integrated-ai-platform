#!/bin/bash
# Daily Restic backup to MinIO on QNAP (192.168.10.201:9000)
# Requires: vault unsealed, MinIO running on QNAP, restic installed
# Schedule: launchd or cron at 02:00

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
LOG_PREFIX="[backup $(date '+%Y-%m-%d %H:%M:%S')]"

log() { echo "$LOG_PREFIX $*"; }

# Fetch credentials from Vault
VAULT_TOKEN=$(cat ~/vault-init-keys.txt | grep "Initial Root Token" | awk '{print $NF}')

vault_get() {
  docker exec -e VAULT_TOKEN="$VAULT_TOKEN" vault-server vault kv get -field="$2" "$1" 2>/dev/null
}

export AWS_ACCESS_KEY_ID=$(vault_get secret/minio/backup access_key)
export AWS_SECRET_ACCESS_KEY=$(vault_get secret/minio/backup secret_key)
export RESTIC_PASSWORD=$(vault_get secret/restic/backup password)
export RESTIC_REPOSITORY="s3:http://192.168.10.201:9000/backups"

BACKUP_DIRS=(
  "$HOME/repos/integrated-ai-platform/config"
  "$HOME/repos/integrated-ai-platform/docs"
  "$HOME/repos/integrated-ai-platform/docker/caddy"
  "$HOME/repos/integrated-ai-platform/docker/headscale"
  "$HOME/repos/integrated-ai-platform/scripts"
)

log "Starting backup to $RESTIC_REPOSITORY"
restic backup "${BACKUP_DIRS[@]}" \
  --tag daily \
  --exclude-caches \
  --verbose 2>&1

log "Pruning old snapshots (keep 30 daily, 12 monthly)"
restic forget \
  --keep-daily 30 \
  --keep-monthly 12 \
  --prune 2>&1

log "Backup complete"
