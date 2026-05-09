#!/usr/bin/env bash
# OpenCode wrapper: execute task and capture schema-compliant artifacts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
TASK_BRIEF=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --task-brief) TASK_BRIEF="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "$TASK_BRIEF" ]]; then
  echo "Usage: $0 --task-brief <path>"
  exit 1
fi

if [[ ! -f "$TASK_BRIEF" ]]; then
  echo "Error: task brief not found: $TASK_BRIEF"
  exit 1
fi

# Extract task metadata
TASK_ID=$(jq -r '.task_id' "$TASK_BRIEF")
WORKTREE=$(jq -r '.worktree' "$TASK_BRIEF")
REPO=$(jq -r '.repo' "$TASK_BRIEF")

if [[ -z "$TASK_ID" ]] || [[ "$TASK_ID" == "null" ]]; then
  echo "Error: task_id not found in brief"
  exit 1
fi

# Create run directory
RUN_DIR="$HOME/local-ai-workstation/agent_runs/${TASK_ID}/opencode"
mkdir -p "$RUN_DIR"

# Emit pre-run artifact
PRE_RUN=$(cat <<EOF
{
  "task_id": "$TASK_ID",
  "agent": "opencode",
  "timestamp_start": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "worktree": "$WORKTREE",
  "repo": "$REPO",
  "status": "started",
  "artifact_type": "pre_run"
}
EOF
)
echo "$PRE_RUN" > "$RUN_DIR/artifact-pre-run.json"

# Run OpenCode in the worktree
echo "[OpenCode] Starting task $TASK_ID in $WORKTREE"
cd "$WORKTREE"

# Capture exit code
EXIT_CODE=0
DURATION=0
START_TIME=$(date +%s)

if /opt/homebrew/bin/opencode --config 2>&1 | tee "$RUN_DIR/execution.log"; then
  RESULT="success"
else
  EXIT_CODE=$?
  RESULT="failure"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Emit post-run artifact
POST_RUN=$(cat <<EOF
{
  "task_id": "$TASK_ID",
  "agent": "opencode",
  "timestamp_end": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "worktree": "$WORKTREE",
  "repo": "$REPO",
  "status": "$RESULT",
  "exit_code": $EXIT_CODE,
  "duration_seconds": $DURATION,
  "artifact_type": "post_run"
}
EOF
)
echo "$POST_RUN" > "$RUN_DIR/artifact-post-run.json"

echo "[OpenCode] Task $TASK_ID completed with status: $RESULT (exit $EXIT_CODE, ${DURATION}s)"
echo "[OpenCode] Artifacts written to: $RUN_DIR"

exit $EXIT_CODE
