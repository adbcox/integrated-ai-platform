#!/usr/bin/env bash
# Block 2.5 P2.1 — provision Vault policy, AppRole, and operator
# password for the control-plane service.
#
# Idempotent: safe to re-run. Will not overwrite an existing operator
# password unless OPERATOR_RESET=1.
#
# Run on Mac Mini (or via SSH from the dev host with VAULT_TOKEN set).
# Doctrine: hash-only verification, no value display.

set -euo pipefail

DOCKER=/opt/homebrew/bin/docker
VAULT_TOKEN=${VAULT_TOKEN:-$(/bin/cat ~/.vault-token)}
SERVICE=control-plane
APPROLE_DIR="/Users/admin/.vault-approle/${SERVICE}"
SECRETS_DIR="/Users/admin/.vault-agent-secrets/${SERVICE}"
POLICY_FILE="config/vault-policies/${SERVICE}-policy.hcl"

log() { printf '[provision-control-plane] %s\n' "$*"; }

if [ ! -r "${POLICY_FILE}" ]; then
  log "ERROR: policy file ${POLICY_FILE} not found (run from repo root)"
  exit 1
fi

# ── Step 1: write policy ──────────────────────────────────────────────
log "writing policy ${SERVICE}"
${DOCKER} cp "${POLICY_FILE}" vault-server:/tmp/${SERVICE}-policy.hcl
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault policy write ${SERVICE} /tmp/${SERVICE}-policy.hcl

# ── Step 2: create or update AppRole ──────────────────────────────────
log "creating/updating AppRole ${SERVICE}"
${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault write auth/approle/role/${SERVICE} \
    token_policies=${SERVICE} \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_ttl=0

# ── Step 3: capture role-id + secret-id ──────────────────────────────
mkdir -p "${APPROLE_DIR}"
chmod 0700 "${APPROLE_DIR}"

if [ ! -s "${APPROLE_DIR}/role-id" ]; then
  log "writing role-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault read -field=role_id auth/approle/role/${SERVICE}/role-id \
    > "${APPROLE_DIR}/role-id"
  chmod 0600 "${APPROLE_DIR}/role-id"
else
  log "role-id already present (skipping)"
fi

if [ ! -s "${APPROLE_DIR}/secret-id" ]; then
  log "writing secret-id"
  ${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault write -force -field=secret_id \
      auth/approle/role/${SERVICE}/secret-id \
    > "${APPROLE_DIR}/secret-id"
  chmod 0600 "${APPROLE_DIR}/secret-id"
else
  log "secret-id already present (skipping)"
fi

# ── Step 4: host secrets directory ────────────────────────────────────
mkdir -p "${SECRETS_DIR}"
chmod 0700 "${SECRETS_DIR}"

# ── Step 5: operator password (Argon2 hash) ───────────────────────────
EXISTING_HASH=$(${DOCKER} exec -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
  vault kv get -field=argon2_hash secret/control-plane/operator 2>/dev/null || true)

if [ -n "${EXISTING_HASH}" ] && [ "${OPERATOR_RESET:-0}" != "1" ]; then
  log "operator password already set (re-run with OPERATOR_RESET=1 to change)"
else
  log "operator password setup (set OPERATOR_RESET=1 in env to overwrite)"
  log "you will be prompted twice; password is read with no echo"

  # Read password twice into a tmp file via a child python
  # process. Plaintext never reaches a shell variable that could be
  # logged or surfaced.
  TMP_HASH_FILE=$(mktemp -t cp-hash-XXXXXXXX)
  trap 'rm -f "${TMP_HASH_FILE}"' EXIT

  python3 - <<'PY' >"${TMP_HASH_FILE}"
import getpass, sys
try:
    from argon2 import PasswordHasher
except ImportError:
    sys.stderr.write("argon2-cffi not installed; install with: pip3 install --user argon2-cffi\n")
    sys.exit(2)

p1 = getpass.getpass("Operator password: ")
p2 = getpass.getpass("Confirm:           ")
if p1 != p2:
    sys.stderr.write("ERROR: passwords do not match\n")
    sys.exit(3)
if len(p1) < 12:
    sys.stderr.write("ERROR: password must be >= 12 chars\n")
    sys.exit(4)

print(PasswordHasher().hash(p1), end="")
PY

  HASH=$(/bin/cat "${TMP_HASH_FILE}")
  if [ -z "${HASH}" ]; then
    log "ERROR: hash empty (Python script failed)"
    exit 5
  fi

  # Write to Vault via stdin to avoid hash appearing in process args
  ${DOCKER} exec -i -e VAULT_TOKEN="${VAULT_TOKEN}" vault-server \
    vault kv put secret/control-plane/operator argon2_hash=- <<<"${HASH}" >/dev/null

  HASH_PREFIX=$(printf '%s' "${HASH}" | shasum -a 256 | awk '{print substr($1,1,12)}')
  log "operator password written; hash sha256 prefix: ${HASH_PREFIX}"
fi

# ── Step 6: verify policy isolation ───────────────────────────────────
log "verifying isolation (read in-policy + denied out-of-policy)"
ROLE_ID=$(/bin/cat "${APPROLE_DIR}/role-id")
SECRET_ID=$(/bin/cat "${APPROLE_DIR}/secret-id")

CP_TOKEN=$(${DOCKER} exec vault-server vault write -field=token \
  auth/approle/login role_id="${ROLE_ID}" secret_id="${SECRET_ID}")

if [ -z "${CP_TOKEN}" ]; then
  log "ERROR: AppRole login failed"
  exit 6
fi

# In-policy: read operator hash → success
if ${DOCKER} exec -e VAULT_TOKEN="${CP_TOKEN}" vault-server \
     vault kv get -field=argon2_hash secret/control-plane/operator >/dev/null 2>&1; then
  log "  ✅ in-policy read (control-plane/operator) succeeded"
else
  log "  ❌ in-policy read failed — policy attached incorrectly"
  exit 7
fi

# Out-of-policy: read vault root token sink → denied
if ${DOCKER} exec -e VAULT_TOKEN="${CP_TOKEN}" vault-server \
     vault kv get secret/headscale/admin >/dev/null 2>&1; then
  log "  ❌ out-of-policy read SUCCEEDED — policy is too permissive"
  exit 8
else
  log "  ✅ out-of-policy read (headscale/admin) denied"
fi

# Out-of-policy: policy modification → denied
if ${DOCKER} exec -e VAULT_TOKEN="${CP_TOKEN}" vault-server \
     vault policy write control-plane-test /tmp/${SERVICE}-policy.hcl >/dev/null 2>&1; then
  log "  ❌ policy write SUCCEEDED — explicit-deny block missing"
  exit 9
else
  log "  ✅ policy write denied"
fi

# Revoke the verification token
${DOCKER} exec -e VAULT_TOKEN="${CP_TOKEN}" vault-server \
  vault token revoke -self >/dev/null 2>&1 || true

log "P2.1 provisioning complete"
