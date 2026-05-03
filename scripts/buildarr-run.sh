#!/usr/bin/env bash
# Buildarr one-shot config sync for arr-stack (Radarr + Prowlarr).
# Invoked by launchd plist com.iap.buildarr-sync (daily at 03:00).
# Also callable manually:
#   scripts/buildarr-run.sh          — live apply
#   scripts/buildarr-run.sh --check  — test-config only (no mutations)
#
# D-17-44: Buildarr config-as-code substrate (§18.G component 2)
# Doctrine: D-17-38 Vault Agent sidecar pattern; D-17-29 container DNS.

set -euo pipefail

REPO=/Users/admin/repos/integrated-ai-platform
TEMPLATE="${REPO}/config/arr-stack/buildarr/buildarr.yml"
SECRETS_DIR=/Users/admin/.vault-agent-secrets/buildarr
APPROLE_DIR=/Users/admin/.vault-approle/buildarr
DOCKER=/opt/homebrew/bin/docker
NETWORK=control-center-net
IMAGE=callum027/buildarr:latest
LOG_DIR=/Users/admin/.platform-logs
RENDERED=/tmp/buildarr-rendered-$$.yml

CHECK_ONLY=false
if [ "${1:-}" = "--check" ]; then
  CHECK_ONLY=true
fi

log() { printf '[buildarr-run] %s\n' "$*"; }

# ── Step 1: refresh Vault Agent credentials ──────────────────────────
log "step 1: refreshing Vault Agent credentials"
${DOCKER} run --rm \
  --network "${NETWORK}" \
  -e VAULT_ADDR="http://vault-server:8200" \
  -e SKIP_SETCAP="true" \
  -v "${APPROLE_DIR}:/vault/approle:ro" \
  -v "${SECRETS_DIR}:/vault/secrets" \
  -v "${REPO}/docker/vault-agent-buildarr/agent.hcl:/vault/config/agent.hcl:ro" \
  -v "${REPO}/docker/vault-agent-buildarr/credentials.env.tmpl:/vault/agent-config/credentials.env.tmpl:ro" \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  hashicorp/vault:2.0.0 agent -config=/vault/config/agent.hcl 2>&1 | \
    grep -E "ERROR|WARN|template server stopped" || true
log "  credentials.env refreshed"

# ── Step 2: copy template to secrets volume for substitution ─────────
cp "${TEMPLATE}" "${SECRETS_DIR}/buildarr-repo.yml"

# ── Step 3: run Buildarr (test-config or live run) ───────────────────
BUILDARR_CMD="run"
if [ "${CHECK_ONLY}" = "true" ]; then
  BUILDARR_CMD="test-config"
  log "step 2: running buildarr test-config (--check mode, no mutations)"
else
  log "step 2: running buildarr run (live apply)"
fi

${DOCKER} run --rm \
  --network "${NETWORK}" \
  -v "${SECRETS_DIR}:/vault/secrets:ro" \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --entrypoint sh \
  "${IMAGE}" \
  -c "
set -eu
set -a && . /vault/secrets/credentials.env && set +a
python3 -c \"
import os, re
src = open('/vault/secrets/buildarr-repo.yml').read()
rendered = re.sub(r'\\\\\\\$\{([A-Z_]+)\}', lambda m: os.environ[m.group(1)], src)
open('/tmp/buildarr-rendered.yml', 'w').write(rendered)
\"
exec buildarr ${BUILDARR_CMD} /tmp/buildarr-rendered.yml
" 2>&1
RC=$?

# ── Step 4: heartbeat for launchd monitoring ─────────────────────────
mkdir -p "${LOG_DIR}"
if [ ${RC} -eq 0 ]; then
  touch "${LOG_DIR}/buildarr-sync.heartbeat"
  log "done (exit 0)"
else
  log "FAILED (exit ${RC})"
  exit ${RC}
fi
