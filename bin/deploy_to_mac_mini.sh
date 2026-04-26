#!/usr/bin/env bash
# deploy_to_mac_mini.sh — Deploy the Master Control Panel stack to Mac Mini
#
# Deploys: Homepage + AI Platform Dashboard + Traefik + docker-socket-proxy
# Requires: Docker Desktop on Mac Mini, SSH key auth set up
#
# Usage:
#   ./bin/deploy_to_mac_mini.sh                  # full deploy
#   ./bin/deploy_to_mac_mini.sh --dashboard-only  # just the AI dashboard
#   ./bin/deploy_to_mac_mini.sh --dry-run         # preview without applying
#
# Environment:
#   MAC_MINI_HOST   SSH target (default: mac-mini.local)
#   MAC_MINI_USER   SSH user   (default: current user)
#   REPO_PATH       Remote repo path (default: ~/repos/integrated-ai-platform)

set -euo pipefail

MAC_MINI_HOST="${MAC_MINI_HOST:-mac-mini.local}"
MAC_MINI_USER="${MAC_MINI_USER:-$(whoami)}"
REPO_PATH="${REPO_PATH:-~/repos/integrated-ai-platform}"
COMPOSE_FILE="docker/docker-compose-dashboards.yml"
DASHBOARD_ONLY=false
DRY_RUN=false

log()  { echo "[deploy-mini] $*"; }
warn() { echo "[deploy-mini] WARN: $*" >&2; }
die()  { echo "[deploy-mini] ERROR: $*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --dashboard-only) DASHBOARD_ONLY=true ;;
    --dry-run)        DRY_RUN=true ;;
    --help)
      grep "^#" "$0" | head -20 | sed 's/^# \?//'
      exit 0 ;;
  esac
done

SSH="ssh -o StrictHostKeyChecking=no ${MAC_MINI_USER}@${MAC_MINI_HOST}"
REMOTE="$SSH"

log "Target: ${MAC_MINI_USER}@${MAC_MINI_HOST}"
log "Repo path: ${REPO_PATH}"

# ── 1. Verify connectivity ─────────────────────────────────────────────────
log "Checking SSH connectivity..."
$REMOTE "echo connected" || die "Cannot SSH to ${MAC_MINI_HOST}. Check MAC_MINI_HOST and key auth."

# ── 2. Verify Docker is running ────────────────────────────────────────────
log "Checking Docker..."
$REMOTE "docker info > /dev/null 2>&1" || die "Docker not running on ${MAC_MINI_HOST}"
log "Docker OK"

# ── 3. Sync repo changes ───────────────────────────────────────────────────
log "Syncing repository..."
if $DRY_RUN; then
  log "[DRY-RUN] Would git pull on ${MAC_MINI_HOST}:${REPO_PATH}"
else
  $REMOTE "cd ${REPO_PATH} && git pull --ff-only"
  log "Repo synced"
fi

# ── 4. Create .env if missing ──────────────────────────────────────────────
ENV_EXISTS=$($REMOTE "test -f ${REPO_PATH}/docker/.env && echo yes || echo no")
if [[ "$ENV_EXISTS" == "no" ]]; then
  warn ".env not found — copying from .env.example"
  if $DRY_RUN; then
    log "[DRY-RUN] Would copy .env.example → .env"
  else
    $REMOTE "cp ${REPO_PATH}/docker/.env.example ${REPO_PATH}/docker/.env"
    log "Created docker/.env — edit it to set EXECUTOR_HOST and API keys"
  fi
fi

# ── 5. Create required host directories ───────────────────────────────────
log "Creating homelab directories..."
if ! $DRY_RUN; then
  $REMOTE "mkdir -p ~/homelab/traefik/certs ~/homelab/homepage/config"
fi

# ── 6. Deploy ─────────────────────────────────────────────────────────────
if $DASHBOARD_ONLY; then
  DEPLOY_SERVICES="ai-platform-dashboard"
  COMPOSE_CMD="docker compose -f ${REPO_PATH}/${COMPOSE_FILE} up -d --build ${DEPLOY_SERVICES}"
else
  COMPOSE_CMD="docker compose -f ${REPO_PATH}/${COMPOSE_FILE} up -d --build"
fi

log "Deploying${DASHBOARD_ONLY:+ (dashboard only)}..."
if $DRY_RUN; then
  log "[DRY-RUN] Would run: ${COMPOSE_CMD}"
else
  $REMOTE "cd ${REPO_PATH} && ${COMPOSE_CMD}"
  log "Deploy complete"
fi

# ── 7. Verify health ───────────────────────────────────────────────────────
if ! $DRY_RUN; then
  log "Waiting for dashboard health check..."
  DASHBOARD_PORT=$($REMOTE "cd ${REPO_PATH} && grep -E '^DASHBOARD_PORT=' docker/.env 2>/dev/null | cut -d= -f2" || echo "8080")
  DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"

  for i in $(seq 1 12); do
    STATUS=$($REMOTE "curl -sf http://localhost:${DASHBOARD_PORT}/api/health 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[\"status\"])' 2>/dev/null || echo pending")
    if [[ "$STATUS" == "ok" ]]; then
      log "Dashboard healthy at http://${MAC_MINI_HOST}:${DASHBOARD_PORT}"
      break
    fi
    [[ $i -lt 12 ]] && sleep 5 || warn "Dashboard health check timed out — check: docker logs ai-platform-dashboard"
  done

  HOMEPAGE_PORT=$($REMOTE "cd ${REPO_PATH} && grep -E '^HOMEPAGE_PORT=' docker/.env 2>/dev/null | cut -d= -f2" || echo "3000")
  HOMEPAGE_PORT="${HOMEPAGE_PORT:-3000}"
  log "Homepage (if deployed): http://${MAC_MINI_HOST}:${HOMEPAGE_PORT}"
fi

log "Done."
