#!/usr/bin/env bash
# D-17-49 — Cleanuparr API-driven config bootstrap (no UI session).
#
# Behavior overview:
#   1. Reads admin api_key from rendered Vault sidecar credentials
#      (D-17-76 commit-2 sidecar template).
#   2. Reads rTorrent creds (URL/username/password) from Vault sidecar.
#   3. Idempotently registers ONE rTorrent download client via
#      POST /api/configuration/download_client/.
#      (Cleanuparr does not support SABnzbd in the deployed image —
#      Usenet path is platform-canonical but out-of-scope for Cleanuparr;
#      tracked as known limitation in docs/phase-18/d-17-49/SMOKE.md.)
#   4. PUTs `/api/configuration/seeker` to enable Seeker + per-instance
#      enable for sonarr/radarr (conservative caps already pre-staged).
#   5. Confirms Queue Cleaner + Download Cleaner remain disabled
#      (initial-deploy safety; require operator post-Seeker observation
#      cycle before flip).
#   6. With `--enable-cleaners` flag (post-observation operator action):
#      PUTs `/api/configuration/queue_cleaner` + `/api/configuration/download_cleaner`
#      with `enabled: true`.
#
# Idempotency: GET clients before POST; if a client with matching name
# already exists, no-op. Seeker PUT is naturally idempotent (full-state
# replacement).
#
# Hash-only verification per F6 doctrine — never echo api_key, password,
# or other credential values.
#
# Usage:
#   ./scripts/cleanuparr-bootstrap-config.sh                 # initial bootstrap (Seeker on, Cleaners off)
#   ./scripts/cleanuparr-bootstrap-config.sh --enable-cleaners # post-observation flip
#
# Exit codes: 0 success; 2 missing creds; 3 unexpected API failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUPARR_API="${SCRIPT_DIR}/cleanuparr-api.sh"

ENABLE_CLEANERS=0
if [ "${1:-}" = "--enable-cleaners" ]; then
  ENABLE_CLEANERS=1
fi

CRED_FILE="/Users/admin/.vault-agent-secrets/cleanuparr/credentials.env"

log() { printf '[cleanuparr-bootstrap] %s\n' "$*"; }
hash12() {
  python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])" "$1"
}

if [ ! -r "${CRED_FILE}" ]; then
  log "ERROR: ${CRED_FILE} not readable. Vault Agent sidecar must have rendered first."
  log "       Run \`docker compose up -d vault-agent-cleanuparr\` and verify it Exited(0)."
  exit 2
fi

# shellcheck disable=SC1090
. "${CRED_FILE}"

if [ -z "${CLEANUPARR_API_KEY:-}" ]; then
  log "ERROR: CLEANUPARR_API_KEY not set in ${CRED_FILE}"
  exit 2
fi
log "credentials sourced; CLEANUPARR_API_KEY sha256[:12]=$(hash12 "${CLEANUPARR_API_KEY}")"

if [ -z "${RTORRENT_URL:-}" ]; then
  log "ERROR: RTORRENT_URL not set in ${CRED_FILE}; sidecar template missing the rtorrent block"
  exit 2
fi
log "RTORRENT_URL sha256[:12]=$(hash12 "${RTORRENT_URL}")"

export CLEANUPARR_API_KEY RTORRENT_URL RTORRENT_USER RTORRENT_PASSWORD

# ── Helpers ──────────────────────────────────────────────────────────────────
api() { "${CLEANUPARR_API}" "$@"; }

# Parse RTORRENT_URL into host + port + urlBase + useSsl. Cleanuparr's
# download_client schema separates these fields rather than accepting a
# full URL string. Accepts forms like:
#   https://5.nl19.seedit4.me/rutorrent/plugins/httprpc/action.php
#   http://host:8080/rutorrent/plugins/httprpc/action.php
#   scgi://host:5000/  (rare, not common on seedit4me)
parse_url() {
  local url="$1"
  python3 - "$url" <<'PY'
import sys
from urllib.parse import urlparse
p = urlparse(sys.argv[1])
host = p.hostname or ""
scheme = p.scheme or "https"
use_ssl = "true" if scheme == "https" else "false"
port = p.port
if port is None:
    port = 443 if scheme == "https" else 80
url_base = p.path or ""
print(f"HOST={host}")
print(f"PORT={port}")
print(f"URL_BASE={url_base}")
print(f"USE_SSL={use_ssl}")
PY
}

# ── Step 1: register rTorrent download client (idempotent) ──────────────────
RT_CLIENT_NAME="rtorrent-seedbox"

EXISTING=$(api GET /api/configuration/download_client/ \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('|'.join(c.get('id','')+':'+c.get('name','') for c in d.get('clients',[])))")
log "existing clients: ${EXISTING:-<none>}"

if echo "${EXISTING}" | grep -q ":${RT_CLIENT_NAME}\b"; then
  log "rTorrent client \"${RT_CLIENT_NAME}\" already registered — skipping POST"
else
  log "registering rTorrent client \"${RT_CLIENT_NAME}\""
  eval "$(parse_url "${RTORRENT_URL}")"

  POST_BODY=$(python3 -c '
import json,os,sys
body = {
  "name": sys.argv[1],
  "enabled": True,
  "typeName": "rTorrent",
  "host": sys.argv[2],
  "port": int(sys.argv[3]),
  "username": os.environ.get("RTORRENT_USER",""),
  "password": os.environ.get("RTORRENT_PASSWORD",""),
  "urlBase": sys.argv[4],
  "useSsl": sys.argv[5] == "true",
  "newClient": {}
}
print(json.dumps(body))
' "${RT_CLIENT_NAME}" "${HOST}" "${PORT}" "${URL_BASE}" "${USE_SSL}")

  RESP=$(api POST /api/configuration/download_client/ "${POST_BODY}")
  if echo "${RESP}" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("id") else 1)' 2>/dev/null; then
    NEW_ID=$(echo "${RESP}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
    log "registered rTorrent client id=${NEW_ID}"
  else
    log "ERROR: POST download_client/ unexpected response:"
    echo "${RESP}" | head -c 500
    echo
    exit 3
  fi
fi

# ── Step 2: enable Seeker (full-state PUT) ──────────────────────────────────
log "enabling Seeker (searchEnabled=true; per-instance enable=true)"
SEEKER_BODY=$(api GET /api/configuration/seeker | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["searchEnabled"] = True
for inst in cfg.get("instances", []):
    inst["enabled"] = True
print(json.dumps(cfg))
')
SEEKER_RESP=$(api PUT /api/configuration/seeker "${SEEKER_BODY}")
log "seeker PUT response head: $(echo "${SEEKER_RESP}" | head -c 120)"

# ── Step 3: ensure Cleaners disabled (initial bootstrap) OR enable on flag ──
if [ "${ENABLE_CLEANERS}" = "1" ]; then
  log "--enable-cleaners: enabling Queue Cleaner + Download Cleaner"

  QC_BODY=$(api GET /api/configuration/queue_cleaner | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["enabled"] = True
print(json.dumps(cfg))
')
  api PUT /api/configuration/queue_cleaner "${QC_BODY}" >/dev/null
  log "queue_cleaner enabled=true"

  DC_BODY=$(api GET /api/configuration/download_cleaner | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["enabled"] = True
print(json.dumps(cfg))
')
  api PUT /api/configuration/download_cleaner "${DC_BODY}" >/dev/null
  log "download_cleaner enabled=true"
else
  QC_ENABLED=$(api GET /api/configuration/queue_cleaner | python3 -c 'import json,sys; print(json.load(sys.stdin).get("enabled",False))')
  DC_ENABLED=$(api GET /api/configuration/download_cleaner | python3 -c 'import json,sys; print(json.load(sys.stdin).get("enabled",False))')
  log "queue_cleaner enabled=${QC_ENABLED} (expected: False at initial bootstrap)"
  log "download_cleaner enabled=${DC_ENABLED} (expected: False at initial bootstrap)"
fi

# ── Step 4: confirm safety posture ──────────────────────────────────────────
DRY_RUN=$(api GET /api/configuration/general | python3 -c 'import json,sys; print(json.load(sys.stdin).get("dryRun",False))')
log "general.dryRun=${DRY_RUN} (expected: True until operator authorizes live actions)"

unset CLEANUPARR_API_KEY RTORRENT_URL RTORRENT_USER RTORRENT_PASSWORD SEEDBOX_PASSWORD
log "complete"
