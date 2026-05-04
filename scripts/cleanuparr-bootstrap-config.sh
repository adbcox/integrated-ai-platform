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
#   6. With `--enable-cleaners` flag (post-observation operator action,
#      D-17-86 close): PUTs `/api/configuration/queue_cleaner` +
#      `/api/configuration/download_cleaner` with `enabled: true` AND
#      PUTs `/api/configuration/general` with `dryRun: false`. Stock
#      cron expressions are preserved verbatim (queue=every 5 min,
#      download=top of hour) — WP-03 doctrine kept stock values; this
#      script does not author cron mutations.
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

# Parse RTORRENT_URL into host (FULL scheme://hostname[:port] origin) +
# url_base (path-only). Cleanuparr's `download_clients` table schema has
# columns: id, enabled, name, type_name, type, host, username, password,
# url_base, external_url — explicitly NO `port` and NO `use_ssl` columns
# (verified via SQLite inspection at D-17-86 WP-07). The model's
# `get_Url()` accessor concatenates `host + url_base` and parses the
# result as a System.Uri; if `host` is a bare hostname, the parse throws
# `Invalid URI: The format of the URI could not be determined.`
#
# Doctrine consequence: the POST body uses `host` as a FULL ORIGIN
# (scheme + hostname + optional port), not a bare hostname. The legacy
# parse_url() that emitted separate HOST/PORT/USE_SSL was sending fields
# Cleanuparr silently discards (no DB column to land in) while leaving
# `host` as a bare hostname that fails URI parsing on first health check.
# This anti-pattern produced two unhealthy clients (D-17-86 WP-07
# discovery sequence) before the schema-truth check landed it.
#
# Accepts forms like:
#   https://5.nl19.seedit4.me/rutorrent/plugins/httprpc/action.php
#   http://host:8080/rutorrent/plugins/httprpc/action.php
parse_url() {
  local url="$1"
  python3 - "$url" <<'PY'
import sys
from urllib.parse import urlparse
p = urlparse(sys.argv[1])
host_only = p.hostname or ""
scheme = p.scheme or "https"
# Build FULL origin (scheme + hostname + optional port). Omit explicit
# port when it matches the scheme default — Cleanuparr stores host as a
# string and feeds it to System.Uri, which is more forgiving with
# canonical-default-port URLs.
origin_parts = [scheme, "://", host_only]
if p.port is not None:
    default_port = 443 if scheme == "https" else 80
    if p.port != default_port:
        origin_parts.append(f":{p.port}")
origin = "".join(origin_parts)
url_base = p.path or ""
print(f"HOST={origin}")
print(f"URL_BASE={url_base}")
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
  "type": "Torrent",
  "host": sys.argv[2],
  "username": os.environ.get("RTORRENT_USER",""),
  "password": os.environ.get("RTORRENT_PASSWORD",""),
  "urlBase": sys.argv[3],
}
print(json.dumps(body))
' "${RT_CLIENT_NAME}" "${HOST}" "${URL_BASE}")

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
# When --enable-cleaners is passed, this is the operator-authorization flip
# (D-17-86): post-Seeker observation gate satisfied. Bundle Cleaner enable
# with general.dryRun=false so the cleaners start producing real actions on
# their next cron tick. Stock cron values are kept verbatim (queue=every 5
# min, download=top of hour) per WP-03 doctrine — no schedule mutation here.
if [ "${ENABLE_CLEANERS}" = "1" ]; then
  log "--enable-cleaners: enabling Queue Cleaner + Download Cleaner + flipping dryRun=false"

  QC_BODY=$(api GET /api/configuration/queue_cleaner | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["enabled"] = True
print(json.dumps(cfg))
')
  api PUT /api/configuration/queue_cleaner "${QC_BODY}" >/dev/null
  log "queue_cleaner enabled=true (cron preserved)"

  DC_BODY=$(api GET /api/configuration/download_cleaner | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["enabled"] = True
print(json.dumps(cfg))
')
  api PUT /api/configuration/download_cleaner "${DC_BODY}" >/dev/null
  log "download_cleaner enabled=true (cron preserved)"

  GEN_BODY=$(api GET /api/configuration/general | python3 -c '
import json,sys
cfg = json.load(sys.stdin)
cfg["dryRun"] = False
print(json.dumps(cfg))
')
  api PUT /api/configuration/general "${GEN_BODY}" >/dev/null
  log "general.dryRun=false (live actions authorized)"
else
  QC_ENABLED=$(api GET /api/configuration/queue_cleaner | python3 -c 'import json,sys; print(json.load(sys.stdin).get("enabled",False))')
  DC_ENABLED=$(api GET /api/configuration/download_cleaner | python3 -c 'import json,sys; print(json.load(sys.stdin).get("enabled",False))')
  log "queue_cleaner enabled=${QC_ENABLED} (expected: False at initial bootstrap)"
  log "download_cleaner enabled=${DC_ENABLED} (expected: False at initial bootstrap)"
fi

# ── Step 4: report safety posture ───────────────────────────────────────────
# Expected dryRun depends on path:
#   initial bootstrap (no flag)  → dryRun=true  (operator hasn't authorized live yet)
#   --enable-cleaners            → dryRun=false (set explicitly above)
DRY_RUN=$(api GET /api/configuration/general | python3 -c 'import json,sys; print(json.load(sys.stdin).get("dryRun",False))')
if [ "${ENABLE_CLEANERS}" = "1" ]; then
  log "general.dryRun=${DRY_RUN} (expected: False after --enable-cleaners)"
else
  log "general.dryRun=${DRY_RUN} (expected: True until operator authorizes live actions)"
fi

unset CLEANUPARR_API_KEY RTORRENT_URL RTORRENT_USER RTORRENT_PASSWORD SEEDBOX_PASSWORD
log "complete"
