#!/usr/bin/env bash
# OpenCode wrapper: execute task and capture schema-compliant artifacts per §7

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_BRIEF=""
MODE="${MODE:-build}"  # plan, build, ask
while [[ $# -gt 0 ]]; do
  case $1 in
    --task-brief) TASK_BRIEF="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "$TASK_BRIEF" ]]; then
  echo "Usage: $0 --task-brief <path> [--mode plan|build|ask]"
  exit 1
fi

if [[ ! -f "$TASK_BRIEF" ]]; then
  echo "Error: task brief not found: $TASK_BRIEF"
  exit 1
fi

# Extract task metadata per §10.6 schema
TASK_ID=$(jq -r '.task_id' "$TASK_BRIEF")
TASK_CLASS=$(jq -r '.task_class // "simple_edit"' "$TASK_BRIEF")
WORKTREE=$(jq -r '.worktree' "$TASK_BRIEF")
REPO=$(jq -r '.repo' "$TASK_BRIEF")
PERMISSIONS=$(jq -r '.permissions_profile // "eval_edit"' "$TASK_BRIEF")

if [[ -z "$TASK_ID" ]] || [[ "$TASK_ID" == "null" ]]; then
  echo "Error: task_id not found in brief"
  exit 1
fi

# Resolve host information
HOST=$(hostname -s)

# Runtime resolution: probe for available endpoint
probe_model_host() {
  if curl -s -m 2 http://10.55.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Thunderbolt"
    return 0
  elif curl -s -m 2 http://192.168.10.142:11434/api/tags >/dev/null 2>&1; then
    echo "LAN"
    return 0
  elif curl -s -m 2 http://localhost:4000/v1/models >/dev/null 2>&1; then
    echo "LiteLLM-local"
    return 0
  fi
  echo "none"
  return 1
}

MODEL_HOST=$(probe_model_host)
case "$MODEL_HOST" in
  Thunderbolt) ENDPOINT="http://10.55.0.1:11434" ;;
  LAN) ENDPOINT="http://192.168.10.142:11434" ;;
  LiteLLM-local) ENDPOINT="http://localhost:4000" ;;
  *) ENDPOINT=""; MODEL_HOST="none" ;;
esac

# Model selection: extract from task brief, fallback to default
BRIEF_MODEL=$(jq -r '.model // null' "$TASK_BRIEF")
if [[ "$BRIEF_MODEL" != "null" && -n "$BRIEF_MODEL" ]]; then
  MODEL="$BRIEF_MODEL"
else
  MODEL="qwen3-coder:30b-coding"
fi

# E-003 substitution: translate canonical model names to LiteLLM model names
if [[ "$MODEL_HOST" == "LiteLLM-local" ]]; then
  case "$MODEL" in
    qwen3-coder:30b-coding|qwen3-coder:30b|ollama_chat/qwen3-coder:30b-coding)
      LITELLM_MODEL="qwen3-coder-30b" ;;
    qwen3-coder-next:80B|ollama_chat/qwen3-coder-next:80B)
      LITELLM_MODEL="qwen3-coder-30b" ;;
    deepseek-coder-v2:16b|ollama_chat/deepseek-coder-v2:16b)
      LITELLM_MODEL="qwen2.5-coder" ;;
    gemma2:27b)
      LITELLM_MODEL="qwen2.5-coder" ;;
    *)
      LITELLM_MODEL="qwen2.5-coder" ;;
  esac
  MODEL="$LITELLM_MODEL"
  PROVIDER="litellm"
fi

# Provider derivation from model prefix or MODEL_HOST
if [[ "$MODEL" =~ ^litellm/ ]]; then
  PROVIDER="litellm"
elif [[ "$MODEL" =~ ^ollama ]]; then
  PROVIDER="ollama"
elif [[ "$MODEL_HOST" == "LiteLLM-local" ]]; then
  PROVIDER="litellm"
elif [[ "$MODEL_HOST" == "none" ]]; then
  PROVIDER="unknown"
else
  PROVIDER="ollama"
fi

# Create run directory
RUN_DIR="$HOME/local-ai-workstation/agent_runs/${TASK_ID}/opencode"
mkdir -p "$RUN_DIR"

# Resolve OpenCode binary path
OPENCODE_BIN="${OPENCODE_BIN:-$HOME/.opencode/bin/opencode}"
if [[ ! -x "$OPENCODE_BIN" ]]; then
  echo "Error: opencode binary not found at $OPENCODE_BIN. Set OPENCODE_BIN env var."
  exit 1
fi

# Get agent version
AGENT_VERSION=$("$OPENCODE_BIN" --version 2>/dev/null | head -1 || echo "unknown")

# Pre-run artifact per §7
TIMESTAMP_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PRE_RUN=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP_START",
  "task_id": "$TASK_ID",
  "agent": "opencode",
  "agent_version": "$AGENT_VERSION",
  "host": "$HOST",
  "model_host": "$MODEL_HOST",
  "provider": "$PROVIDER",
  "model": "$MODEL",
  "endpoint": "$ENDPOINT",
  "repo": "$REPO",
  "worktree": "$WORKTREE",
  "branch": "$(cd "$WORKTREE" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "task_class": "$TASK_CLASS",
  "mode": "$MODE",
  "permissions_profile": "$PERMISSIONS",
  "verifier_status": "not_run",
  "notes": "Pre-run initialization"
}
EOF
)
echo "$PRE_RUN" > "$RUN_DIR/artifact-pre-run.json"

echo "[OpenCode] Starting task $TASK_ID (mode: $MODE) in $WORKTREE"

# Execute OpenCode per §9.4: cd to worktree and launch opencode
EXIT_CODE=0
DURATION=0
START_TIME=$(date +%s)
TASK_SUMMARY=$(jq -r '.task_summary' "$TASK_BRIEF")

# Apply operational mode prefix per §9.6 (mode selection via prompt)
case "$MODE" in
  plan)
    TASK_SUMMARY="Plan only. Do not edit files yet. $TASK_SUMMARY"
    ;;
  ask)
    TASK_SUMMARY="Inspect only. Do not edit files. $TASK_SUMMARY"
    ;;
  build)
    # build mode: no prefix
    ;;
esac

cd "$WORKTREE"

# Capture files before
FILES_BEFORE=$(find . -type f -name '*.py' -o -name '*.js' -o -name '*.json' 2>/dev/null | sort || true)

# Run OpenCode with task summary as message
if [[ "$MODEL_HOST" == "LiteLLM-local" ]]; then
  "$OPENCODE_BIN" run "$TASK_SUMMARY" --dir "$WORKTREE" --model "litellm_local/$MODEL" 2>&1 | tee "$RUN_DIR/execution.log"
else
  "$OPENCODE_BIN" run "$TASK_SUMMARY" --dir "$WORKTREE" 2>&1 | tee "$RUN_DIR/execution.log"
fi
PIPE_EXIT=${PIPESTATUS[0]}
if [[ $PIPE_EXIT -eq 0 ]]; then
  RESULT="pass"
  VERIFIER="pass"
else
  EXIT_CODE=$PIPE_EXIT
  RESULT="fail"
  VERIFIER="fail"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Capture files after
FILES_AFTER=$(find . -type f -name '*.py' -o -name '*.js' -o -name '*.json' 2>/dev/null | sort || true)

# Compute diff
MODIFIED_FILES=$(comm -13 <(echo "$FILES_BEFORE") <(echo "$FILES_AFTER") | head -20 || true)
LINES_ADDED=$(grep -c '^+' "$RUN_DIR/execution.log" 2>/dev/null) || LINES_ADDED=0
LINES_REMOVED=$(grep -c '^-' "$RUN_DIR/execution.log" 2>/dev/null) || LINES_REMOVED=0

# Post-run artifact per §7
TIMESTAMP_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
POST_RUN=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP_END",
  "task_id": "$TASK_ID",
  "agent": "opencode",
  "agent_version": "$AGENT_VERSION",
  "host": "$HOST",
  "model_host": "$MODEL_HOST",
  "provider": "$PROVIDER",
  "model": "$MODEL",
  "endpoint": "$ENDPOINT",
  "repo": "$REPO",
  "worktree": "$WORKTREE",
  "branch": "$(cd "$WORKTREE" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "task_class": "$TASK_CLASS",
  "mode": "$MODE",
  "permissions_profile": "$PERMISSIONS",
  "files_modified": $(echo "$MODIFIED_FILES" | jq -Rs 'split("\n")[:-1]'),
  "diff_lines_added": $LINES_ADDED,
  "diff_lines_removed": $LINES_REMOVED,
  "wall_clock_seconds": $DURATION,
  "malformed_edit_count": 0,
  "operator_interventions": 0,
  "rollback_available": true,
  "verifier_status": "$VERIFIER",
  "notes": "OpenCode execution completed"
}
EOF
)
echo "$POST_RUN" > "$RUN_DIR/artifact-post-run.json"

echo "[OpenCode] Task $TASK_ID completed with verifier status: $VERIFIER (${DURATION}s)"
echo "[OpenCode] Artifacts: $RUN_DIR"

exit $EXIT_CODE
