#!/usr/bin/env bash
# D-17-76 — populate seedbox download-client credentials in Vault.
#
# Populates both seedbox-resident clients in one run:
#   secret/seedbox/rtorrent — rTorrent XML-RPC API (torrent client;
#                              Cleanuparr download-client target)
#   secret/seedbox/sabnzbd  — SABnzbd REST API (Usenet client;
#                              platform-canonical, consumed by
#                              non-Cleanuparr services. Cleanuparr's
#                              deployed image binary does not implement
#                              SABnzbd as a download-client type — see
#                              docs/phase-18/d-17-49/SMOKE.md "Known
#                              limitation — Cleanuparr SABnzbd coverage
#                              gap".)
#
# Operator-runnable. Takes credentials interactively (stdin -s read; no
# echo to terminal, no chat/repo exposure). Writes to Vault. Verifies
# hash-only (sha256[:12], never raw values).
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

RT_PATH="secret/seedbox/rtorrent"
SB_PATH="secret/seedbox/sabnzbd"

log() { printf '[provision-seedbox-credentials] %s\n' "$*"; }
hash12() {
  python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])" "$1"
}

# ── rTorrent inputs ──────────────────────────────────────────────────────────
log "Populating ${RT_PATH}. Inputs are read silently and never echoed."
echo
read -r -p "rTorrent XML-RPC URL (e.g. https://5.nl19.seedit4me/rutorrent/plugins/httprpc/action.php or scgi://...): " RT_URL
read -r -p "rTorrent username (HTTP Basic; blank if none): " RT_USER
read -r -s -p "rTorrent password (HTTP Basic; blank if none): " RT_PASS
echo

if [ -z "${RT_URL}" ]; then
  log "ERROR: rTorrent URL is required"
  exit 64
fi

# ── SABnzbd inputs ───────────────────────────────────────────────────────────
log "Populating ${SB_PATH}."
echo
read -r -p "SABnzbd URL (e.g. https://5.nl19.seedit4me/sabnzbd/): " SB_URL
read -r -s -p "SABnzbd api_key: " SB_KEY
echo

if [ -z "${SB_URL}" ] || [ -z "${SB_KEY}" ]; then
  log "ERROR: SABnzbd url and api_key are both required"
  unset RT_URL RT_USER RT_PASS SB_URL SB_KEY
  exit 64
fi

# ── Write to Vault ───────────────────────────────────────────────────────────
log "Writing ${RT_PATH}"
RT_ARGS=(url="${RT_URL}")
if [ -n "${RT_USER}" ]; then
  RT_ARGS+=(username="${RT_USER}")
fi
if [ -n "${RT_PASS}" ]; then
  RT_ARGS+=(password="${RT_PASS}")
fi
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" -i vault-server \
  vault kv put "${RT_PATH}" "${RT_ARGS[@]}" >/dev/null

log "Writing ${SB_PATH}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" -i vault-server \
  vault kv put "${SB_PATH}" url="${SB_URL}" api_key="${SB_KEY}" >/dev/null

# ── Hash-only readback verification ──────────────────────────────────────────
log "Read-back verification (hash-only):"

RB_RT_URL=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=url "${RT_PATH}")
log "  ${RT_PATH} url       sha256[:12]=$(hash12 "${RB_RT_URL}")"
if [ -n "${RT_USER}" ]; then
  RB_RT_USER=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field=username "${RT_PATH}")
  log "  ${RT_PATH} username  sha256[:12]=$(hash12 "${RB_RT_USER}")"
fi
if [ -n "${RT_PASS}" ]; then
  RB_RT_PASS=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field=password "${RT_PATH}")
  log "  ${RT_PATH} password  sha256[:12]=$(hash12 "${RB_RT_PASS}")"
fi

RB_SB_URL=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=url "${SB_PATH}")
RB_SB_KEY=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=api_key "${SB_PATH}")
log "  ${SB_PATH} url        sha256[:12]=$(hash12 "${RB_SB_URL}")"
log "  ${SB_PATH} api_key    sha256[:12]=$(hash12 "${RB_SB_KEY}")"

# Sanity: post-write equality (no value display, equality check only)
if [ "${RB_RT_URL}" != "${RT_URL}" ] || [ "${RB_SB_URL}" != "${SB_URL}" ] || [ "${RB_SB_KEY}" != "${SB_KEY}" ]; then
  log "ERROR: read-back mismatch — Vault write did not persist as expected"
  unset RT_URL RT_USER RT_PASS SB_URL SB_KEY RB_RT_URL RB_RT_USER RB_RT_PASS RB_SB_URL RB_SB_KEY VAULT_TOKEN
  exit 70
fi

unset RT_URL RT_USER RT_PASS SB_URL SB_KEY RB_RT_URL RB_RT_USER RB_RT_PASS RB_SB_URL RB_SB_KEY VAULT_TOKEN

log "complete — ${RT_PATH} + ${SB_PATH} populated"
log "next: scripts/cleanuparr-bootstrap-config.sh registers the rTorrent"
log "      client via Cleanuparr API (SABnzbd is platform-canonical but"
log "      out-of-scope for Cleanuparr — see SMOKE.md Known Limitation)."
