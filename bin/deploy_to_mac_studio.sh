#!/usr/bin/env bash
# deploy_to_mac_studio.sh — Set up the compute/model services on Mac Studio
#
# Configures: Ollama, executor worker environment, Glances (system monitor)
# Does NOT deploy Docker dashboards — those live on Mac Mini.
#
# Usage:
#   ./bin/deploy_to_mac_studio.sh               # full setup
#   ./bin/deploy_to_mac_studio.sh --ollama-only  # just Ollama check/restart
#   ./bin/deploy_to_mac_studio.sh --dry-run      # preview without applying
#
# Environment:
#   MAC_STUDIO_HOST   SSH target (default: mac-studio.local)
#   MAC_STUDIO_USER   SSH user   (default: current user)
#   REPO_PATH         Remote repo path (default: ~/repos/integrated-ai-platform)
#   OLLAMA_MODEL      Default model to pull (default: qwen2.5-coder:14b)

set -euo pipefail

MAC_STUDIO_HOST="${MAC_STUDIO_HOST:-mac-studio.local}"
MAC_STUDIO_USER="${MAC_STUDIO_USER:-$(whoami)}"
REPO_PATH="${REPO_PATH:-~/repos/integrated-ai-platform}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-coder:14b}"
OLLAMA_ONLY=false
DRY_RUN=false

log()  { echo "[deploy-studio] $*"; }
warn() { echo "[deploy-studio] WARN: $*" >&2; }
die()  { echo "[deploy-studio] ERROR: $*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --ollama-only) OLLAMA_ONLY=true ;;
    --dry-run)     DRY_RUN=true ;;
    --help)
      grep "^#" "$0" | head -20 | sed 's/^# \?//'
      exit 0 ;;
  esac
done

SSH="ssh -o StrictHostKeyChecking=no ${MAC_STUDIO_USER}@${MAC_STUDIO_HOST}"
REMOTE="$SSH"

log "Target: ${MAC_STUDIO_USER}@${MAC_STUDIO_HOST}"

# ── 1. Verify connectivity ─────────────────────────────────────────────────
log "Checking SSH connectivity..."
$REMOTE "echo connected" || die "Cannot SSH to ${MAC_STUDIO_HOST}. Check MAC_STUDIO_HOST and key auth."

# ── 2. Check / start Ollama ────────────────────────────────────────────────
log "Checking Ollama..."
OLLAMA_RUNNING=$($REMOTE "curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo yes || echo no")
if [[ "$OLLAMA_RUNNING" == "yes" ]]; then
  log "Ollama already running"
else
  log "Ollama not running — attempting to start..."
  if $DRY_RUN; then
    log "[DRY-RUN] Would run: ollama serve &"
  else
    $REMOTE "nohup ollama serve > /tmp/ollama.log 2>&1 &"
    sleep 3
    OLLAMA_RUNNING=$($REMOTE "curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 && echo yes || echo no")
    [[ "$OLLAMA_RUNNING" == "yes" ]] && log "Ollama started" || warn "Ollama may not have started — check /tmp/ollama.log"
  fi
fi

# ── 3. Pull default model if not present ──────────────────────────────────
log "Checking model: ${OLLAMA_MODEL}..."
MODEL_PRESENT=$($REMOTE "ollama list 2>/dev/null | grep -q '${OLLAMA_MODEL%:*}' && echo yes || echo no")
if [[ "$MODEL_PRESENT" == "no" ]]; then
  log "Pulling ${OLLAMA_MODEL} (this may take a while)..."
  if $DRY_RUN; then
    log "[DRY-RUN] Would run: ollama pull ${OLLAMA_MODEL}"
  else
    $REMOTE "ollama pull ${OLLAMA_MODEL}"
    log "Model pulled"
  fi
else
  log "Model ${OLLAMA_MODEL} already present"
fi

if $OLLAMA_ONLY; then
  log "Done (ollama only)."
  exit 0
fi

# ── 4. Sync repo ───────────────────────────────────────────────────────────
log "Syncing repository..."
if $DRY_RUN; then
  log "[DRY-RUN] Would git pull on ${MAC_STUDIO_HOST}:${REPO_PATH}"
else
  REPO_EXISTS=$($REMOTE "test -d ${REPO_PATH}/.git && echo yes || echo no")
  if [[ "$REPO_EXISTS" == "yes" ]]; then
    $REMOTE "cd ${REPO_PATH} && git pull --ff-only"
    log "Repo synced"
  else
    warn "Repo not found at ${REPO_PATH} — clone it first:"
    warn "  ssh ${MAC_STUDIO_USER}@${MAC_STUDIO_HOST} 'git clone https://github.com/adbcox/integrated-ai-platform ${REPO_PATH}'"
  fi
fi

# ── 5. Verify Python environment ───────────────────────────────────────────
log "Checking Python environment..."
PYTHON_OK=$($REMOTE "python3 --version > /dev/null 2>&1 && echo yes || echo no")
[[ "$PYTHON_OK" == "yes" ]] && log "Python OK" || warn "Python3 not found on ${MAC_STUDIO_HOST}"

# ── 6. Install Glances (system monitor for Homepage widget) ───────────────
log "Checking Glances..."
GLANCES_OK=$($REMOTE "glances --version > /dev/null 2>&1 && echo yes || echo no")
if [[ "$GLANCES_OK" == "no" ]]; then
  log "Installing Glances..."
  if $DRY_RUN; then
    log "[DRY-RUN] Would run: pip3 install glances[web]"
  else
    $REMOTE "pip3 install --user 'glances[web]'" && log "Glances installed"
  fi
fi

# ── 7. Start Glances web server (port 61208) ──────────────────────────────
GLANCES_RUNNING=$($REMOTE "curl -sf http://localhost:61208/ > /dev/null 2>&1 && echo yes || echo no")
if [[ "$GLANCES_RUNNING" == "no" ]]; then
  log "Starting Glances web server..."
  if $DRY_RUN; then
    log "[DRY-RUN] Would run: glances -w &"
  else
    $REMOTE "nohup glances -w --disable-plugin all --enable-plugin cpu,mem,fs,network > /tmp/glances.log 2>&1 &"
    log "Glances started on port 61208"
  fi
else
  log "Glances already running"
fi

# ── 8. Summary ────────────────────────────────────────────────────────────
log ""
log "Mac Studio services:"
log "  Ollama:    http://${MAC_STUDIO_HOST}:11434"
log "  Glances:   http://${MAC_STUDIO_HOST}:61208"
log ""
log "To point the dashboard at Mac Studio, set in docker/.env on Mac Mini:"
log "  EXECUTOR_HOST=${MAC_STUDIO_HOST}"
log "  OLLAMA_HOST=${MAC_STUDIO_HOST}:11434"
log ""
log "Done."
