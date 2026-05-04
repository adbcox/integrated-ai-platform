#!/usr/bin/env bash
# D-17-87 — provision Vault policy/AppRole for Lidarr integration substrate.
# Hash-only verification: sha256[:12], never print raw credential values.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
source "$(dirname "$0")/lib/vault-admin-token.sh"
VAULT_TOKEN=$(resolve_admin_vault_token) || exit 2
SERVICE=lidarr
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-lidarr] %s\n' "$*"; }

sha12() {
  python3 - <<'PY' "$1"
import hashlib,sys
print(hashlib.sha256(sys.argv[1].encode()).hexdigest()[:12])
PY
}

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

log "step 1: writing Vault policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl >/dev/null

log "step 2: creating/updating AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} token_ttl=1h token_max_ttl=4h secret_id_ttl=0 >/dev/null

mkdir -p "${APPROLE_DIR}" "${SECRETS_DIR}"
chmod 0700 "${APPROLE_DIR}" "${SECRETS_DIR}"

if [ ! -s "${APPROLE_DIR}/role-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id > "${APPROLE_DIR}/role-id"
  chmod 0600 "${APPROLE_DIR}/role-id"
fi

if [ ! -s "${APPROLE_DIR}/secret-id" ]; then
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault write -force -field=secret_id auth/approle/role/${SERVICE}/secret-id > "${APPROLE_DIR}/secret-id"
  chmod 0600 "${APPROLE_DIR}/secret-id"
fi

log "step 3: AppRole read test (hash-only)"
ROLE_ID=$(cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(cat "${APPROLE_DIR}/secret-id")
TEST_TOKEN=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write -format=json auth/approle/login role_id="${ROLE_ID}" secret_id="${SECRET_ID}" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth']['client_token'])")

PROWLARR_VAL=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server \
  vault kv get -field=api_key secret/arr/prowlarr)
log "  secret/arr/prowlarr readable sha256[:12]=$(sha12 "${PROWLARR_VAL}")"

LIDARR_VAL=$(${DOCKER} exec -e VAULT_TOKEN="${TEST_TOKEN}" vault-server \
  vault kv get -field=api_key secret/arr/lidarr 2>/dev/null || true)
if [ -n "${LIDARR_VAL}" ]; then
  log "  secret/arr/lidarr readable sha256[:12]=$(sha12 "${LIDARR_VAL}")"
else
  log "  secret/arr/lidarr not present yet (expected pre-first-boot)"
fi

unset ROLE_ID SECRET_ID TEST_TOKEN PROWLARR_VAL LIDARR_VAL
log "step 4: optional post-deploy Lidarr download-client category enforcement"

# Idempotent guard: only run if Lidarr API is reachable on localhost.
LIDARR_API_KEY=$(${DOCKER} exec lidarr sh -lc "grep -oPm1 '(?<=<ApiKey>)[^<]+' /config/config.xml" 2>/dev/null || true)
if [ -z "${LIDARR_API_KEY}" ]; then
  log "  lidarr API key unavailable (container not up yet) — skipping category enforcement"
  log "provision-lidarr complete"
  exit 0
fi

python3 - <<'PY' "${VAULT_TOKEN}" "${LIDARR_API_KEY}" "${DOCKER}"
import json
import subprocess
import sys
import urllib.parse
import urllib.request

vault_token, lidarr_api_key, docker_bin = sys.argv[1], sys.argv[2], sys.argv[3]
base = "http://127.0.0.1:8686/api/v1"


def http_get(path: str):
    with urllib.request.urlopen(f"{base}{path}?apikey={lidarr_api_key}", timeout=20) as r:
        return json.load(r)


def http_put(path: str, body: dict):
    req = urllib.request.Request(
        f"{base}{path}?apikey={lidarr_api_key}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def http_post(path: str, body: dict):
    req = urllib.request.Request(
        f"{base}{path}?apikey={lidarr_api_key}",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.load(r)


def vault_get_json(path: str):
    raw = subprocess.run(
        [docker_bin, "exec", "-e", f"VAULT_TOKEN={vault_token}", "vault-server", "sh", "-lc", f"vault kv get -format=json {path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(raw)["data"]["data"]


def set_field(obj: dict, name: str, value):
    for f in obj.get("fields", []):
        if f.get("name") == name:
            f["value"] = value
            return True
    return False


clients = http_get("/downloadclient")
by_impl = {c.get("implementation"): c for c in clients}
schema = http_get("/downloadclient/schema")

# Ensure SAB is category-segregated for Lidarr.
sab = by_impl.get("Sabnzbd")
if sab:
    changed = set_field(sab, "musicCategory", "lidarr")
    if changed:
        http_put(f"/downloadclient/{sab['id']}", sab)

# Ensure rTorrent category and directory stay canonical.
rt = by_impl.get("RTorrent")
if rt:
    changed = False
    changed |= set_field(rt, "musicCategory", "lidarr")
    changed |= set_field(rt, "musicDirectory", "/downloads/rtorrent/lidarr")
    if changed:
        http_put(f"/downloadclient/{rt['id']}", rt)

# Ensure remote path mappings exist so Docker path checks pass.
rpm = http_get("/remotepathmapping")
need = [
    {"host": "5.nl19.seedit4.me", "remotePath": "/home/seedit4me/torrents/rtorrent/", "localPath": "/downloads/rtorrent/"},
    {"host": "5.nl19.seedit4.me", "remotePath": "/home/seedit4me/sabnzbd/complete/lidarr/", "localPath": "/downloads/sabnzbd/lidarr/"},
]
for n in need:
    if not any(
        m.get("host") == n["host"]
        and m.get("remotePath") == n["remotePath"]
        and m.get("localPath") == n["localPath"]
        for m in rpm
    ):
        http_post("/remotepathmapping", n)
PY

log "provision-lidarr complete"
