#!/usr/bin/env bash
# Goose wrapper: execute orchestration recipe and capture schema-compliant artifacts per §7, §10.5

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_BRIEF=""
RECIPE_PATH=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --task-brief) TASK_BRIEF="$2"; shift 2;;
    --recipe) RECIPE_PATH="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "$TASK_BRIEF" ]] || [[ -z "$RECIPE_PATH" ]]; then
  echo "Usage: $0 --task-brief <path> --recipe <recipe_path>"
  exit 1
fi

if [[ ! -f "$TASK_BRIEF" ]]; then
  echo "Error: task brief not found: $TASK_BRIEF"
  exit 1
fi

if [[ ! -f "$RECIPE_PATH" ]]; then
  echo "Error: recipe not found: $RECIPE_PATH"
  exit 1
fi

# Extract task metadata per §10.6
TASK_ID=$(jq -r '.task_id' "$TASK_BRIEF")
TASK_CLASS=$(jq -r '.task_class // "simple_edit"' "$TASK_BRIEF")
WORKTREE=$(jq -r '.worktree' "$TASK_BRIEF")
REPO=$(jq -r '.repo' "$TASK_BRIEF")
PERMISSIONS=$(jq -r '.permissions_profile // "eval_edit"' "$TASK_BRIEF")
TASK_SUMMARY=$(jq -r '.task_summary' "$TASK_BRIEF")

if [[ -z "$TASK_ID" ]] || [[ "$TASK_ID" == "null" ]]; then
  echo "Error: task_id not found in brief"
  exit 1
fi

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

RUN_DIR="$HOME/local-ai-workstation/agent_runs/${TASK_ID}/goose"
mkdir -p "$RUN_DIR"

AGENT_VERSION=$(goose --version 2>/dev/null | head -1 || echo "unknown")

TIMESTAMP_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PRE_RUN=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP_START",
  "task_id": "$TASK_ID",
  "agent": "goose",
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
  "mode": "recipe",
  "permissions_profile": "$PERMISSIONS",
  "verifier_status": "not_run",
  "notes": "Pre-run initialization"
}
EOF
)
echo "$PRE_RUN" > "$RUN_DIR/artifact-pre-run.json"

echo "[Goose] Starting recipe for task $TASK_ID in $WORKTREE"

EXIT_CODE=0
DURATION=0
START_TIME=$(date +%s)

cd "$WORKTREE"

# Verifier pre-state capture (git-diff-based; replaces broken find+comm+grep
# verifier pre-2026-05-11). The prior logic missed untracked files outside
# .py/.js/.json, missed in-place modifications entirely, and counted lines
# by grepping Goose stdout for ^+ — every run reported files_modified=[""]
# + diff_lines_added=0 + verifier_status=pass regardless of actual outcome.
# Mirrors the canonical wrap-opencode fix in commit 1ce59ffc.
PRE_REF=$(git rev-parse HEAD 2>/dev/null || echo "")

# Extract recipe parameters and build --params string
PARAMS_STRING="task_id=$TASK_ID task_summary=$TASK_SUMMARY worktree=$WORKTREE"

# Extract recipe parameter names
for PARAM_NAME in $(grep "  - name:" "$RECIPE_PATH" | sed 's/.*- name: //'); do
  if [[ -z "$PARAM_NAME" ]]; then
    continue
  fi

  # Skip if already in params
  if [[ -z "${PARAMS_STRING##*$PARAM_NAME=*}" ]]; then
    continue
  fi

  # Check if parameter is required and has default
  PARAM_REQUIRED=$(sed -n "/  - name: $PARAM_NAME/,/  - name:/p" "$RECIPE_PATH" | grep -q "required: true" && echo "1" || echo "0")
  PARAM_DEFAULT=$(sed -n "/  - name: $PARAM_NAME/,/  - name:/p" "$RECIPE_PATH" | grep "default:" | sed 's/.*default: "\(.*\)"/\1/')

  # Try to get value from task brief
  BRIEF_VALUE=$(jq -r ".${PARAM_NAME} // null" "$TASK_BRIEF" 2>/dev/null || echo "null")

  if [[ "$BRIEF_VALUE" != "null" && -n "$BRIEF_VALUE" ]]; then
    PARAMS_STRING="$PARAMS_STRING $PARAM_NAME=$BRIEF_VALUE"
  elif [[ -n "$PARAM_DEFAULT" ]]; then
    PARAMS_STRING="$PARAMS_STRING $PARAM_NAME=$PARAM_DEFAULT"
  elif [[ "$PARAM_REQUIRED" == "1" ]]; then
    echo "Error: required recipe parameter '$PARAM_NAME' not found in task brief and no default provided"
    exit 1
  fi
done

if [[ "$MODEL_HOST" == "LiteLLM-local" ]]; then
  export GOOSE_PROVIDER=openai
  export OPENAI_HOST="http://localhost:4000"
  export OPENAI_API_KEY="sk-local-only-not-secret"  # pragma: allowlist secret
  export GOOSE_MODEL="$MODEL"
else
  export GOOSE_PROVIDER=ollama
  export OLLAMA_HOST="$ENDPOINT"
  export GOOSE_MODEL="$MODEL"
fi

if goose run --recipe "$RECIPE_PATH" --params $PARAMS_STRING 2>&1 | tee "$RUN_DIR/execution.log"; then
  RESULT=${PIPESTATUS[0]}
  VERIFIER="pass"
else
  RESULT=${PIPESTATUS[0]}
  VERIFIER="fail"
fi

if [[ $RESULT -eq 0 ]]; then
  EXIT_CODE=0
else
  EXIT_CODE=$RESULT
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Verifier post-state diff (git-diff-based; honest detection across all file
# types including untracked + in-place modifications). See pre-state comment above.
PORCELAIN=$(git status --porcelain 2>/dev/null || true)

# files_modified: parse porcelain. Handles M / A / D / R / ?? entries.
# Rename lines ("R  old -> new") yield the new path.
MODIFIED_FILES=$(echo "$PORCELAIN" | awk 'NF>0 {
  path=substr($0,4)
  n=index(path," -> ")
  if (n>0) path=substr(path,n+4)
  print path
}' | sort -u | head -50)

# Untracked files need intent-only-add (-N) to participate in git diff;
# revert after counting so we leave the worktree staging state untouched.
UNTRACKED_LIST=$(echo "$PORCELAIN" | awk 'substr($0,1,2)=="??" {print substr($0,4)}')
if [[ -n "$UNTRACKED_LIST" ]]; then
  echo "$UNTRACKED_LIST" | while IFS= read -r p; do
    [[ -n "$p" ]] && git add -N -- "$p" 2>/dev/null || true
  done
fi

if [[ -n "$PRE_REF" ]]; then
  SHORTSTAT=$(git diff --shortstat "$PRE_REF" 2>/dev/null || echo "")
else
  SHORTSTAT=$(git diff --shortstat 2>/dev/null || echo "")
fi
LINES_ADDED=$(echo "$SHORTSTAT" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "")
LINES_REMOVED=$(echo "$SHORTSTAT" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "")
[[ -z "$LINES_ADDED" ]] && LINES_ADDED=0
[[ -z "$LINES_REMOVED" ]] && LINES_REMOVED=0

if [[ -n "$UNTRACKED_LIST" ]]; then
  echo "$UNTRACKED_LIST" | while IFS= read -r p; do
    [[ -n "$p" ]] && git reset --quiet -- "$p" 2>/dev/null || true
  done
fi

TIMESTAMP_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
POST_RUN=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP_END",
  "task_id": "$TASK_ID",
  "agent": "goose",
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
  "mode": "recipe",
  "permissions_profile": "$PERMISSIONS",
  "files_modified": $(echo "$MODIFIED_FILES" | jq -Rs 'split("\n")[:-1]'),
  "diff_lines_added": $LINES_ADDED,
  "diff_lines_removed": $LINES_REMOVED,
  "wall_clock_seconds": $DURATION,
  "malformed_edit_count": 0,
  "operator_interventions": 0,
  "rollback_available": true,
  "verifier_status": "$VERIFIER",
  "notes": "Goose recipe execution completed"
}
EOF
)
echo "$POST_RUN" > "$RUN_DIR/artifact-post-run.json"

echo "[Goose] Task $TASK_ID completed with verifier status: $VERIFIER (${DURATION}s)"
echo "[Goose] Artifacts: $RUN_DIR"

exit $EXIT_CODE
