#!/usr/bin/env bash
# aider-task.sh — operator entry point for LOCAL_AIDER coding tasks
#
# Usage:
#   scripts/aider-task.sh "task description" [file1 file2 ...]
#   scripts/aider-task.sh --dry-run "task description" [files...]
#   scripts/aider-task.sh --class C1 "task description" [files...]
#   scripts/aider-task.sh --model qwen2.5-coder:32b "task description" [files...]
#   scripts/aider-task.sh --hard "task description" [files...]
#
# Routes through domains/router.py classify. If route is LOCAL_AIDER, invokes
# bin/aider_local.sh. If CLAUDE_CODE escalation, prints guidance and exits 1.
#
# Task classes (--class) align with D-17-90 persona taxonomy:
#   C0  quick lookup / one-liner / ≤1 file (default if 1 file)
#   C1  multi-source synthesis (deliberate-analysis)
#   C2  code/diff review (code-review)
#   C3  planning/decomposition
#   (unset = router infers from description + files)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_CLASS=""
DRY_RUN=0
MODEL_OVERRIDE=""
HARD_MODE=0
DESCRIPTION=""
FILES=()

usage() {
  sed -n '2,20p' "$0" | sed 's/^# //' | sed 's/^#//'
  echo ""
  echo "Model cascade (Mac Mini, in priority order):"
  echo "  qwen2.5-coder:14b  (default fast)"
  echo "  qwen2.5-coder:32b  (--hard or explicit --model)"
  echo "  qwen2.5-coder:7b   (fallback)"
  echo "  devstral:latest    (via --model devstral:latest)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --class)
      TASK_CLASS="$2"; shift 2 ;;
    --class=*)
      TASK_CLASS="${1#--class=}"; shift ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    --model)
      MODEL_OVERRIDE="$2"; shift 2 ;;
    --model=*)
      MODEL_OVERRIDE="${1#--model=}"; shift ;;
    --hard)
      HARD_MODE=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    --)
      shift; break ;;
    -*)
      echo "ERROR: unknown option '$1'" >&2; exit 1 ;;
    *)
      if [[ -z "$DESCRIPTION" ]]; then
        DESCRIPTION="$1"
      else
        FILES+=("$1")
      fi
      shift ;;
  esac
done

if [[ -z "$DESCRIPTION" ]]; then
  echo "ERROR: task description is required" >&2
  usage >&2
  exit 1
fi

# --- Route classification ---
ROUTE_OUTPUT=$(python3 - "$DESCRIPTION" "${FILES[@]}" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domains.router import TaskRouter, ExecutorType

description = sys.argv[1]
files = sys.argv[2:] if len(sys.argv) > 2 else []

router = TaskRouter()
route = router.classify(description, files if files else None)
print(route.executor.value)
print(route.model)
print(f"{route.confidence:.2f}")
print(route.reasoning)
PY
)

EXECUTOR=$(echo "$ROUTE_OUTPUT" | sed -n '1p')
ROUTED_MODEL=$(echo "$ROUTE_OUTPUT" | sed -n '2p')
CONFIDENCE=$(echo "$ROUTE_OUTPUT" | sed -n '3p')
REASONING=$(echo "$ROUTE_OUTPUT" | sed -n '4p')

echo "[aider-task] route: executor=$EXECUTOR model=$ROUTED_MODEL confidence=$CONFIDENCE"
echo "[aider-task] reasoning: $REASONING"

if [[ -n "$TASK_CLASS" ]]; then
  echo "[aider-task] task-class: $TASK_CLASS"
fi

# --- Log to router_events.jsonl with task_class populated ---
RUN_ID="$(date -u +%Y%m%d_%H%M%S)_aider-task_$$"

# Pass all values via env vars to avoid quoting fragility
AIDER_TASK_RUN_ID="$RUN_ID" \
AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
AIDER_TASK_CLASS="$TASK_CLASS" \
AIDER_TASK_EXECUTOR="$EXECUTOR" \
AIDER_TASK_MODEL="$ROUTED_MODEL" \
AIDER_TASK_CONFIDENCE="$CONFIDENCE" \
AIDER_TASK_REASONING="$REASONING" \
AIDER_TASK_DRY_RUN="$DRY_RUN" \
AIDER_TASK_FILES="${FILES[*]+"${FILES[*]}"}" \
python3 - <<'PY'
import json, os, sys
from pathlib import Path

artifact_path = Path("artifacts/aider_runs/router_events.jsonl")
artifact_path.parent.mkdir(parents=True, exist_ok=True)

files_raw = os.environ.get("AIDER_TASK_FILES", "")
files = [f for f in files_raw.split() if f] if files_raw else []

task_class = os.environ.get("AIDER_TASK_CLASS") or None

import time
event = {
    "router_run_id": os.environ["AIDER_TASK_RUN_ID"],
    "api_base": "http://127.0.0.1:11434",
    "task_name": os.environ["AIDER_TASK_DESCRIPTION"],
    "task_class": task_class,
    "executor": os.environ["AIDER_TASK_EXECUTOR"],
    "routed_model": os.environ["AIDER_TASK_MODEL"],
    "confidence": float(os.environ.get("AIDER_TASK_CONFIDENCE", "0")),
    "reasoning": os.environ.get("AIDER_TASK_REASONING", ""),
    "mode": "operator-initiated",
    "files": files,
    "timestamp": int(time.time()),
    "dry_run": os.environ.get("AIDER_TASK_DRY_RUN", "0") == "1",
}

with artifact_path.open("a") as f:
    json.dump(event, f)
    f.write("\n")
print(f"[aider-task] logged event to {artifact_path}")
PY

# --- Escalation path ---
if [[ "$EXECUTOR" != "local_aider" ]]; then
  echo ""
  echo "[aider-task] ESCALATION RECOMMENDED"
  echo "  Route: $EXECUTOR"
  echo "  Reason: $REASONING"
  echo ""
  echo "  This task exceeds LOCAL_AIDER scope. Suggested surface:"
  case "$EXECUTOR" in
    claude_code)
      echo "    claude-local \"$DESCRIPTION\" ${FILES[*]+"${FILES[*]}"}"
      ;;
    claude_chat)
      echo "    Open Claude Code and describe the task interactively."
      ;;
    *)
      echo "    Use Claude Code or another frontier surface."
      ;;
  esac
  exit 1
fi

# --- LOCAL_AIDER path ---
if [[ $DRY_RUN -eq 1 ]]; then
  echo "[aider-task] dry-run: would invoke bin/aider_local.sh with:"
  echo "  --message \"$DESCRIPTION\""
  [[ ${#FILES[@]} -gt 0 ]] && echo "  files: ${FILES[*]}"
  [[ -n "$MODEL_OVERRIDE" ]] && echo "  --model $MODEL_OVERRIDE"
  [[ $HARD_MODE -eq 1 ]] && echo "  --hard"
  exit 0
fi

# Build aider_local.sh invocation
AIDER_ARGS=()

if [[ -n "$MODEL_OVERRIDE" ]]; then
  AIDER_ARGS+=(--model "ollama_chat/$MODEL_OVERRIDE")
elif [[ $HARD_MODE -eq 1 ]]; then
  AIDER_ARGS+=(--hard)
fi

# Message
AIDER_ARGS+=(--message "$DESCRIPTION")

# Files
if [[ ${#FILES[@]} -gt 0 ]]; then
  AIDER_ARGS+=("${FILES[@]}")
fi

echo "[aider-task] invoking: bin/aider_local.sh ${AIDER_ARGS[*]}"
exec bash bin/aider_local.sh "${AIDER_ARGS[@]}"
