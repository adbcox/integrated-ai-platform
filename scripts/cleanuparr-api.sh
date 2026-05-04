#!/usr/bin/env bash
# D-17-49 — thin curl wrapper around Cleanuparr API with X-Api-Key auth.
#
# The Cleanuparr admin api_key authenticates directly against /api/*
# endpoints via the X-Api-Key header — no JWT login flow required for
# api_key-bearing requests. The key is read from Vault at
# secret/cleanuparr/api:key (populated one-time from the running
# container's SQLite admin record by D-17-49 step 4) and either
#   (a) passed to this script via env var CLEANUPARR_API_KEY, OR
#   (b) read from the Vault-rendered sidecar credentials file at
#       /Users/admin/.vault-agent-secrets/cleanuparr/credentials.env
#       (D-17-76 commit-2 sidecar template extension).
#
# Hash-only verification per F6 doctrine — never echo the api_key value.
#
# Usage:
#   cleanuparr-api.sh GET  /api/auth/status
#   cleanuparr-api.sh GET  /api/configuration/download_client/
#   cleanuparr-api.sh POST /api/configuration/download_client/ '{"name":"...","typeName":"rTorrent",...}'
#   cleanuparr-api.sh PUT  /api/configuration/seeker '{...}'
#   cleanuparr-api.sh DELETE /api/configuration/download_client/<id>
#
# Exit codes: 0 success; 2 missing api_key; 3 missing args; 4 curl failure.

set -euo pipefail

CLEANUPARR_BASE_URL="${CLEANUPARR_BASE_URL:-http://localhost:11011}"

resolve_api_key() {
  if [ -n "${CLEANUPARR_API_KEY:-}" ]; then
    printf '%s' "${CLEANUPARR_API_KEY}"
    return 0
  fi
  local cred_file="/Users/admin/.vault-agent-secrets/cleanuparr/credentials.env"
  if [ -r "${cred_file}" ]; then
    local k
    k=$(awk -F= '/^CLEANUPARR_API_KEY=/{ sub(/^CLEANUPARR_API_KEY=/,""); print; exit }' "${cred_file}")
    if [ -n "${k}" ]; then
      printf '%s' "${k}"
      return 0
    fi
  fi
  return 1
}

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <METHOD> <PATH> [BODY_JSON]" >&2
  exit 3
fi

METHOD="$1"
API_PATH="$2"
BODY="${3:-}"

API_KEY="$(resolve_api_key || true)"
if [ -z "${API_KEY}" ]; then
  echo "[cleanuparr-api] ERROR: api_key not in env CLEANUPARR_API_KEY or sidecar credentials.env" >&2
  echo "[cleanuparr-api] hint: source the rendered creds file or export CLEANUPARR_API_KEY before calling" >&2
  exit 2
fi

CURL_ARGS=(
  -sS
  -X "${METHOD}"
  -H "X-Api-Key: ${API_KEY}"
  -H "Accept: application/json"
)
if [ -n "${BODY}" ]; then
  CURL_ARGS+=(-H "Content-Type: application/json" -d "${BODY}")
fi
CURL_ARGS+=("${CLEANUPARR_BASE_URL}${API_PATH}")

curl "${CURL_ARGS[@]}" || { echo "[cleanuparr-api] curl failed" >&2; exit 4; }
