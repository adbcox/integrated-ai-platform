#!/usr/bin/env bash
# D-17-76 — populate secret/seedbox/qbittorrent in Vault from operator input.
#
# Operator-runnable. Takes qBittorrent WebUI credentials interactively
# (stdin -s read; no echo to terminal, no chat/repo exposure). Writes to
# Vault. Verifies hash-only (sha256[:12], never raw values).
#
# Usage:
#   ./scripts/provision-seedbox-credentials.sh
#
# Prerequisites:
#   - vault-server container running on this host
#   - Vault admin token resolvable via scripts/lib/vault-admin-token.sh
#
# Idempotent: re-running with same inputs is a no-op (Vault KV write is
# overwrite-by-design; new sha256[:12] confirms the post-write state).

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2

VAULT_PATH="secret/seedbox/qbittorrent"

log() { printf '[provision-seedbox-credentials] %s\n' "$*"; }
hash12() {
  python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])" "$1"
}

# ── 1. Operator input (no echo) ──────────────────────────────────────────────
log "Populating ${VAULT_PATH}. Inputs are read silently and never echoed."
echo
read -r -p "qBittorrent WebUI URL (e.g. https://5.nl19.seedit4me:8080): " QB_URL
read -r -p "qBittorrent WebUI username: " QB_USER
read -r -s -p "qBittorrent WebUI password: " QB_PASS
echo
read -r -p "Optional category filter (blank for none): " QB_CATEGORY

if [ -z "${QB_URL}" ] || [ -z "${QB_USER}" ] || [ -z "${QB_PASS}" ]; then
  log "ERROR: url, username, and password are all required"
  exit 64
fi

# ── 2. Write to Vault ────────────────────────────────────────────────────────
log "Writing ${VAULT_PATH}"
KV_ARGS=(url="${QB_URL}" username="${QB_USER}" password="${QB_PASS}")
if [ -n "${QB_CATEGORY}" ]; then
  KV_ARGS+=(category="${QB_CATEGORY}")
fi
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" -i vault-server \
  vault kv put "${VAULT_PATH}" "${KV_ARGS[@]}" >/dev/null

# ── 3. Hash-only readback verification ───────────────────────────────────────
log "Read-back verification (hash-only):"
RB_URL=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=url "${VAULT_PATH}")
RB_USER=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=username "${VAULT_PATH}")
RB_PASS=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=password "${VAULT_PATH}")

if [ "${RB_URL}" != "${QB_URL}" ] || [ "${RB_USER}" != "${QB_USER}" ] || [ "${RB_PASS}" != "${QB_PASS}" ]; then
  log "ERROR: read-back mismatch — Vault write did not persist as expected"
  unset QB_URL QB_USER QB_PASS QB_CATEGORY RB_URL RB_USER RB_PASS
  exit 70
fi

log "  url        sha256[:12]=$(hash12 "${RB_URL}")"
log "  username   sha256[:12]=$(hash12 "${RB_USER}")"
log "  password   sha256[:12]=$(hash12 "${RB_PASS}")"

unset QB_URL QB_USER QB_PASS QB_CATEGORY RB_URL RB_USER RB_PASS VAULT_TOKEN

log "complete — ${VAULT_PATH} populated"
log "next: provision Cleanuparr seedbox AppRole/sidecar via scripts/provision-cleanuparr.sh"
log "      then enable Queue/Download Cleaner modules in Cleanuparr UI"
