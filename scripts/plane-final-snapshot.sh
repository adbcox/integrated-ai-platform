#!/usr/bin/env bash
# HISTORICAL / RETIRED SUBSTRATE (Plane CE).
# Do not use for new work. Retained for forensic migration-chain
# verification only.
#
# D-17-04 WP-17-04-02 — final Plane snapshot (DB dump + structured API
# export) prior to substrate replacement by OpenProject.
#
# Outputs:
#   ~/plane-final-snapshot/plane-final-snapshot-YYYY-MM-DD.sql.gz
#       full pg_dump of plane DB. NOT committed — contains password hashes
#       and live API tokens. Hash recorded in the in-repo manifest.
#   docs/_archive/plane-final-snapshot-YYYY-MM-DD.manifest
#       row counts per table + sha256 of the SQL dump for tamper-evidence
#       (committed)
#   docs/_archive/plane-export-YYYY-MM-DD.json
#       structured export from Plane REST API (issues, modules, labels,
#       states, cycles). Public — issue text only, no credentials.
#       Primary input to WP-17-04-03 mapping work. (committed)
#
# Doctrine:
#   - Idempotent re-run: if today's outputs already exist, refuse (forces
#     operator to remove first; prevents accidental overwrite of the
#     forensic snapshot)
#   - All data passes through the script; no operator paste
#   - Token never appears in argv (--config -)
#   - Hash-only verification of completeness
#
# Run on Mac Mini.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
PLANE_DB_CONTAINER=docker-plane-db-1
PLANE_API_BASE="http://localhost:8000"
PLANE_WORKSPACE="iap"
PLANE_PROJECT_ID="dbcd4476-1e37-4812-a443-0914ec8380fc"

DATE=$(/bin/date -u +%Y-%m-%d)
ARCHIVE_DIR="$(cd "$(dirname "$0")/.." && pwd)/docs/_archive"
SQL_DIR="${HOME}/plane-final-snapshot"   # out-of-repo (contains credentials)
SQL_OUT="${SQL_DIR}/plane-final-snapshot-${DATE}.sql.gz"
MANIFEST="${ARCHIVE_DIR}/plane-final-snapshot-${DATE}.manifest"
JSON_OUT="${ARCHIVE_DIR}/plane-export-${DATE}.json"

source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2

log() { printf '[plane-snapshot] %s\n' "$*" >&2; }

# ── Step 0: idempotency / pre-flight ──────────────────────────────────
mkdir -p "${ARCHIVE_DIR}" "${SQL_DIR}"
for f in "${SQL_OUT}" "${MANIFEST}" "${JSON_OUT}"; do
    if [ -e "${f}" ]; then
        log "❌ ${f} already exists; refusing to overwrite forensic snapshot"
        log "   (remove it first if you really want to re-snapshot)"
        exit 1
    fi
done

# ── Step 1: pg_dump → gzip → archive ──────────────────────────────────
log "step 1: pg_dump plane → ${SQL_OUT}"
${DOCKER} exec "${PLANE_DB_CONTAINER}" \
    pg_dump -U plane -d plane --clean --if-exists --no-owner --no-privileges \
    | /usr/bin/gzip -9 > "${SQL_OUT}"
SQL_SIZE=$(/usr/bin/stat -f%z "${SQL_OUT}")
SQL_HASH=$(/usr/bin/shasum -a 256 "${SQL_OUT}" | /usr/bin/awk '{print $1}')
log "  ✅ ${SQL_SIZE} bytes; sha256=${SQL_HASH:0:16}…"

# ── Step 2: per-table row count manifest ──────────────────────────────
log "step 2: collecting row counts → ${MANIFEST}"
{
    printf 'plane-final-snapshot manifest\n'
    printf 'date: %s\n' "${DATE}"
    printf 'sql_path: %s\n' "$(basename "${SQL_OUT}")"
    printf 'sql_size: %s\n' "${SQL_SIZE}"
    printf 'sql_sha256: %s\n' "${SQL_HASH}"
    printf '\nrow counts:\n'
    ${DOCKER} exec "${PLANE_DB_CONTAINER}" psql -U plane -d plane -tAc \
        "SELECT schemaname || '.' || relname || E'\t' || n_live_tup
           FROM pg_stat_user_tables
           WHERE schemaname = 'public'
           ORDER BY n_live_tup DESC, relname ASC" \
        | /usr/bin/awk -F'\t' '$2 > 0 {printf "  %-50s %s\n", $1, $2}'
} > "${MANIFEST}"
TOTAL_ROWS=$(/usr/bin/awk 'NR>6 {s+=$NF} END {print s}' "${MANIFEST}")
log "  ✅ manifest written; total live tuples ≈ ${TOTAL_ROWS}"

# ── Step 3: structured API export (issues + relations) ────────────────
log "step 3: structured Plane API export → ${JSON_OUT}"

# Fetch homepage_token from Vault
PLANE_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv get -field=homepage_token secret/plane/api 2>/dev/null) || {
    log "❌ unable to read secret/plane/api#homepage_token"
    exit 3
}

# API helper — paginates /issues/ (Plane returns {results, next})
api_get() {
    local path="$1"
    local url="${PLANE_API_BASE}${path}"
    /usr/bin/curl -sS -H "X-API-Key: ${PLANE_TOKEN}" "${url}"
}

WS="${PLANE_WORKSPACE}"
PJ="${PLANE_PROJECT_ID}"

# Build the JSON document: workspace + project shells, then collections.
# Use python (system) for safe JSON assembly; data flows via env vars
# and command substitution captures only stringified JSON output.
PYBIN=/usr/bin/python3
PLANE_TOKEN="${PLANE_TOKEN}" PLANE_API_BASE="${PLANE_API_BASE}" \
    WS="${WS}" PJ="${PJ}" \
    "${PYBIN}" - <<'PY' > "${JSON_OUT}"
import json, os, sys, urllib.request, urllib.error

BASE = os.environ["PLANE_API_BASE"]
TOKEN = os.environ["PLANE_TOKEN"]
WS = os.environ["WS"]
PJ = os.environ["PJ"]

def get(path):
    req = urllib.request.Request(f"{BASE}{path}",
        headers={"X-API-Key": TOKEN, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"  HTTP {e.code} on {path}: {e.read()[:200]!r}\n")
        return None

def paginate(path):
    out, page = [], path
    while page:
        r = get(page)
        if r is None:
            break
        if isinstance(r, dict) and "results" in r:
            out.extend(r["results"])
            nxt = r.get("next_page_results")
            cur = r.get("next_cursor") if nxt else None
            if cur:
                joiner = "&" if "?" in path else "?"
                page = f"{path}{joiner}cursor={cur}"
            else:
                page = None
        elif isinstance(r, list):
            out.extend(r); page = None
        else:
            page = None
    return out

base_pj = f"/api/v1/workspaces/{WS}/projects/{PJ}"

doc = {
    "schema_version": 1,
    "source": {"workspace": WS, "project_id": PJ, "api_base": BASE},
    "states":  paginate(f"{base_pj}/states/"),
    "labels":  paginate(f"{base_pj}/labels/"),
    "modules": paginate(f"{base_pj}/modules/"),
    "cycles":  paginate(f"{base_pj}/cycles/"),
    "issues":  paginate(f"{base_pj}/issues/"),
}

for k in ("states", "labels", "modules", "cycles", "issues"):
    sys.stderr.write(f"  fetched {len(doc[k]):>5}  {k}\n")

json.dump(doc, sys.stdout, indent=2, default=str)
PY

unset PLANE_TOKEN

JSON_SIZE=$(/usr/bin/stat -f%z "${JSON_OUT}")
JSON_HASH=$(/usr/bin/shasum -a 256 "${JSON_OUT}" | /usr/bin/awk '{print $1}')
log "  ✅ ${JSON_SIZE} bytes; sha256=${JSON_HASH:0:16}…"

# Append JSON hash to manifest
{
    printf '\njson_export:\n'
    printf '  path: %s\n' "$(basename "${JSON_OUT}")"
    printf '  size: %s\n' "${JSON_SIZE}"
    printf '  sha256: %s\n' "${JSON_HASH}"
} >> "${MANIFEST}"

log "WP-17-04-02 complete:"
log "  SQL (out-of-repo): ${SQL_OUT}"
log "  JSON  (in-repo)  : ${JSON_OUT}"
log "  Manifest (in-repo): ${MANIFEST}"
