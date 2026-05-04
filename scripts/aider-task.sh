#!/usr/bin/env bash
# aider-task.sh — operator entry point for LOCAL_AIDER coding tasks (D-17-94, D-17-96, D-17-97, D-17-103)
#
# Usage:
#   scripts/aider-task.sh "task description" [file1 file2 ...]
#   scripts/aider-task.sh --dry-run "task description" [files...]
#   scripts/aider-task.sh --class C1 "task description" [files...]
#   scripts/aider-task.sh --model qwen3-coder:30b "task description" [files...]
#   scripts/aider-task.sh --hard "task description" [files...]
#   scripts/aider-task.sh --commit "task description" [files...]
#   scripts/aider-task.sh --skip-preflight "task description" [files...]
#   scripts/aider-task.sh --skip-validator "task description" [files...]
#   scripts/aider-task.sh --quiet "task description" [files...]
#
# Routes through domains/router.py classify. If route is LOCAL_AIDER, invokes
# bin/aider_local.sh. If CLAUDE_CODE escalation, prints guidance and exits 1.
#
# Three-layer intelligence (D-17-103):
#   Layer 2 (pre-flight): task shape validator runs before Aider invocation
#     blocks doc-append, rewrite-large, C1-multi-file shapes
#     override: --skip-preflight or AIDER_SKIP_PREFLIGHT=1
#   Layer 1 (post-run diff sanity): aider_guard.py inline checks after Aider runs
#     blocks >2% deletion on append tasks, >30% deletion on general tasks
#     warns on truncation (≤3 lines added to large doc for multi-para task)
#     override: --skip-validator or AIDER_SKIP_VALIDATOR=1
#   Layer 3 (learning loop): records outcome to artifacts/execution_metrics.jsonl
#     feeds domains/learning.py confidence for future routing decisions
#
# Task classes (--class) align with D-17-90 persona taxonomy:
#   C0  quick lookup / one-liner / ≤1 file (default if 1 file)
#   C1  multi-source synthesis (deliberate-analysis)
#   C2  code/diff review (code-review)
#   C3  planning/decomposition
#   (unset = router infers from description + files)
#
# Post-run: Aider edits files but does NOT git-commit (--no-auto-commits).
# After a successful run: git diff <files> → git add <files> → git commit
# Use --commit to have this script run git add + git commit automatically.
#
# Useful Aider in-session commands (run at the > prompt):
#   /diff    show the diff Aider applied
#   /undo    revert the last Aider edit
#   /add <f> add a file to the session context
#   /exit    quit the session
#   /help    list all commands

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_CLASS=""
DRY_RUN=0
MODEL_OVERRIDE=""
HARD_MODE=0
AUTO_COMMIT=0
SKIP_PREFLIGHT=0
SKIP_VALIDATOR=0
ALLOW_LARGE_INSERTIONS=0
QUIET=0
NO_CONTEXT=0
DESCRIPTION=""
FILES=()
AIDER_MESSAGE=""

# Placeholder filenames that indicate a copy-paste template not filled in
PLACEHOLDER_NAMES=("file1" "file1.py" "file1.md" "file2" "file2.py" "file3"
                   "foo" "foo.py" "bar" "bar.md" "baz"
                   "example.py" "test.py" "<file>" "<FILE>" "FILE" "FILE.py")

usage() {
  sed -n '2,27p' "$0" | sed 's/^# //' | sed 's/^#//'
  echo ""
  echo "Examples:"
  echo "  scripts/aider-task.sh --class C0 \"Add docstring to health_check\" services/health.py"
  echo "  scripts/aider-task.sh --class C1 \"Append Related-docs section\" docs/architecture-facts/local-prompt-library-doctrine.md"
  echo "  scripts/aider-task.sh --hard \"Refactor scheduler\" services/scheduler.py"
  echo "  scripts/aider-task.sh --commit --class C0 \"Fix stale hostname\" docs/runbooks/vault-unseal.md"
  echo ""
  echo "Model cascade (Mac Studio 192.168.10.142, in priority order):"
  echo "  qwen3-coder:30b-coding         (default — 30B dense, temp=0.1, ctx=32K, D-17-109)"
  echo "  qwen3-coder-next:coding        (--hard — MoE 79.7B, temp=0.15, ctx=32K)"
  echo "  qwen2.5-coder:7b        (emergency Mac Mini offline fallback only)"
  echo ""
  echo "Override compute target: OLLAMA_API_BASE=http://127.0.0.1:11434 scripts/aider-task.sh ..."
  echo ""
  echo "Tier 1 preset templates: config/prompts/library/v1.0.0/06-aider-tier1-presets.md"
  echo "Full workflow guide:     docs/runbooks/aider-default-workflow.md"
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
    --commit)
      AUTO_COMMIT=1; shift ;;
    --skip-preflight)
      SKIP_PREFLIGHT=1; shift ;;
    --skip-validator)
      SKIP_VALIDATOR=1; shift ;;
    --allow-large-insertions)
      ALLOW_LARGE_INSERTIONS=1; shift ;;
    --no-context)
      NO_CONTEXT=1; shift ;;
    --quiet|-q)
      QUIET=1; shift ;;
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

# --- Placeholder validation (runs before routing to prevent stray file creation) ---
for f in "${FILES[@]}"; do
  basename_f="$(basename "$f")"
  for placeholder in "${PLACEHOLDER_NAMES[@]}"; do
    if [[ "$basename_f" == "$placeholder" ]]; then
      echo "ERROR: '$f' looks like an unfilled template placeholder." >&2
      echo "       Replace with the actual file path before running." >&2
      exit 1
    fi
  done
done

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

if [[ $QUIET -eq 1 ]]; then
  TC_DISPLAY="${TASK_CLASS:-auto}"
  echo "[aider-task] route=$EXECUTOR model=$ROUTED_MODEL conf=$CONFIDENCE class=$TC_DISPLAY"
else
  echo "[aider-task] route: executor=$EXECUTOR model=$ROUTED_MODEL confidence=$CONFIDENCE"
  echo "[aider-task] reasoning: $REASONING"
  if [[ -n "$TASK_CLASS" ]]; then
    echo "[aider-task] task-class: $TASK_CLASS"
  fi
fi

# --- Log to router_events.jsonl with task_class populated ---
RUN_ID="$(date -u +%Y%m%d_%H%M%S)_aider-task_$$"

AIDER_TASK_RUN_ID="$RUN_ID" \
AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
AIDER_TASK_CLASS="$TASK_CLASS" \
AIDER_TASK_EXECUTOR="$EXECUTOR" \
AIDER_TASK_MODEL="$ROUTED_MODEL" \
AIDER_TASK_CONFIDENCE="$CONFIDENCE" \
AIDER_TASK_REASONING="$REASONING" \
AIDER_TASK_DRY_RUN="$DRY_RUN" \
AIDER_TASK_FILES="${FILES[*]+"${FILES[*]}"}" \
AIDER_TASK_QUIET="$QUIET" \
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
if os.environ.get("AIDER_TASK_QUIET") != "1":
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

# --- System context injection (D-17-109) ---
SYSTEM_CTX_FILE="$REPO_ROOT/config/system_knowledge.yaml"
if [[ $NO_CONTEXT -eq 0 ]] && [[ -f "$SYSTEM_CTX_FILE" ]]; then
  SYSTEM_CONTEXT="$(python3 bin/inject_system_context.py --print 2>/dev/null)" || SYSTEM_CONTEXT=""
  if [[ -n "$SYSTEM_CONTEXT" ]]; then
    CTX_CHARS="${#SYSTEM_CONTEXT}"
    AIDER_MESSAGE="${SYSTEM_CONTEXT}"$'\n\n'"${DESCRIPTION}"
    if [[ $QUIET -eq 1 ]]; then
      echo "[aider-task] system-context injected"
    else
      echo "[aider-task] system-context injected (${CTX_CHARS} chars)"
    fi
  else
    AIDER_MESSAGE="$DESCRIPTION"
  fi
else
  AIDER_MESSAGE="$DESCRIPTION"
fi

# --- Layer 2: Pre-flight task shape validator (D-17-103) ---
if [[ $DRY_RUN -eq 0 ]]; then
  PREFLIGHT_RESULT=$(AIDER_SKIP_PREFLIGHT="${AIDER_SKIP_PREFLIGHT:-0}" \
    python3 - "$DESCRIPTION" "$TASK_CLASS" "${FILES[@]+"${FILES[@]}"}" <<'PY'
import sys, os
sys.path.insert(0, ".")
from domains.router import preflight_validate

description = sys.argv[1]
task_class  = sys.argv[2] if len(sys.argv) > 2 else ""
files       = sys.argv[3:] if len(sys.argv) > 3 else []

result = preflight_validate(description, task_class, files if files else None)
print(result.severity)
print(result.shape)
print(result.reason)
PY
  )
  PF_SEVERITY=$(echo "$PREFLIGHT_RESULT" | sed -n '1p')
  PF_SHAPE=$(echo "$PREFLIGHT_RESULT" | sed -n '2p')
  PF_REASON=$(echo "$PREFLIGHT_RESULT" | sed -n '3p')

  if [[ "$PF_SEVERITY" == "block" && "$SKIP_PREFLIGHT" -eq 0 ]]; then
    echo ""
    echo "[aider-task] PRE-FLIGHT BLOCK — shape: $PF_SHAPE"
    echo "  $PF_REASON"
    echo ""
    echo "  Override: scripts/aider-task.sh --skip-preflight ..."
    echo "            or: AIDER_SKIP_PREFLIGHT=1 scripts/aider-task.sh ..."
    exit 3
  elif [[ "$PF_SEVERITY" == "warn" ]]; then
    echo "[aider-task] pre-flight WARN ($PF_SHAPE): $PF_REASON"
  elif [[ "$PF_SEVERITY" == "ok" && "$PF_SHAPE" != "none" ]]; then
    [[ $QUIET -eq 0 ]] && echo "[aider-task] pre-flight: $PF_REASON"
  fi
  [[ $QUIET -eq 1 ]] && echo "[aider-task] preflight=$PF_SEVERITY"
fi

# --- LOCAL_AIDER path ---
if [[ $DRY_RUN -eq 1 ]]; then
  echo "[aider-task] dry-run: would invoke bin/aider_local.sh with:"
  echo "  --message \"${AIDER_MESSAGE:0:120}...(${#AIDER_MESSAGE} chars total)\""
  [[ ${#FILES[@]} -gt 0 ]] && echo "  files: ${FILES[*]}"
  [[ -n "$MODEL_OVERRIDE" ]] && echo "  --model $MODEL_OVERRIDE"
  [[ $HARD_MODE -eq 1 ]] && echo "  --hard"
  [[ $AUTO_COMMIT -eq 1 ]] && echo "  (--commit: will git add + commit after success)"
  exit 0
fi

# Capture pre-run git state for post-run summary
PRE_RUN_HASH=$(git rev-parse HEAD 2>/dev/null || echo "")
if [[ ${#FILES[@]} -gt 0 ]]; then
  PRE_RUN_CHECKSUMS=$(git diff HEAD -- "${FILES[@]}" 2>/dev/null | sha256sum || echo "")
else
  PRE_RUN_CHECKSUMS=""
fi
AIDER_START_TIME=$(date +%s)

# Build aider_local.sh invocation
AIDER_ARGS=()

if [[ -n "$MODEL_OVERRIDE" ]]; then
  AIDER_ARGS+=(--model "ollama_chat/$MODEL_OVERRIDE")
elif [[ $HARD_MODE -eq 1 ]]; then
  AIDER_ARGS+=(--hard)
fi

AIDER_ARGS+=(--message "$AIDER_MESSAGE")

# Disable repo-map for message-mode runs: repo-map discovery causes Aider
# to prompt "Add file to chat?" for related files, which blocks --message
# runs that expect non-interactive execution. Files are passed explicitly.
AIDER_ARGS+=(--map-tokens 0)

if [[ ${#FILES[@]} -gt 0 ]]; then
  AIDER_ARGS+=("${FILES[@]}")
fi

AIDER_QUIET_LOG="/tmp/aider-task-${RUN_ID}.log"
if [[ $QUIET -eq 1 ]]; then
  echo "[aider-task] aider running... (logs: $AIDER_QUIET_LOG)"
else
  echo "[aider-task] invoking: bin/aider_local.sh ${AIDER_ARGS[*]}"
fi

# Run aider (not via exec so we can capture exit code and do post-run work)
set +e
if [[ $QUIET -eq 1 ]]; then
  bash bin/aider_local.sh "${AIDER_ARGS[@]}" >"$AIDER_QUIET_LOG" 2>&1
else
  bash bin/aider_local.sh "${AIDER_ARGS[@]}"
fi
AIDER_EXIT=$?
set -e

AIDER_END_TIME=$(date +%s)
AIDER_DURATION=$(( AIDER_END_TIME - AIDER_START_TIME ))

# --- Post-run summary ---
if [[ $QUIET -eq 0 ]]; then
  echo ""
  echo "[aider-task] --- post-run summary ---"
fi

if [[ $AIDER_EXIT -ne 0 ]]; then
  echo "[aider-task] Aider exited with code $AIDER_EXIT"
  echo "[aider-task] Check output above for errors. If timeout: re-run or use --hard."

  # Layer 3: record failure to learning DB
  AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
  AIDER_TASK_CLASS="${TASK_CLASS:-}" \
  AIDER_TASK_MODEL="$ROUTED_MODEL" \
  AIDER_TASK_DURATION="$AIDER_DURATION" \
  AIDER_TASK_EXIT="$AIDER_EXIT" \
  python3 - <<'PY'
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, ".")
from domains.learning import LearningDomain
error_type = "timeout" if os.environ.get("AIDER_TASK_EXIT") == "124" else "aider_error"
LearningDomain().record_execution(
    task_type="coding",
    description=os.environ.get("AIDER_TASK_DESCRIPTION", "")[:120],
    model=os.environ.get("AIDER_TASK_MODEL", "unknown"),
    executor="LOCAL_AIDER",
    success=False,
    duration_seconds=float(os.environ.get("AIDER_TASK_DURATION", "0")),
    error_type=error_type,
    exit_code=int(os.environ.get("AIDER_TASK_EXIT", "1")),
)
print("[aider-task] learning: recorded failure")
PY
  exit $AIDER_EXIT
fi

# Detect whether files were actually modified
CHANGED_FILES=()
if [[ ${#FILES[@]} -gt 0 ]]; then
  for f in "${FILES[@]}"; do
    if git diff --quiet "$f" 2>/dev/null; then
      : # no change
    else
      CHANGED_FILES+=("$f")
    fi
  done
fi

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  echo "[aider-task] WARNING: Aider made NO changes to the target files."
  echo "[aider-task] Possible causes:"
  echo "  - Model produced a response that didn't match SEARCH/REPLACE format"
  echo "  - Task description too vague — try a more specific instruction"
  echo "  - File context prompts consumed your input (check for 'Add file?' prompts above)"
  echo "[aider-task] Tip: re-run with --hard for a larger model, or refine the description."

  # Layer 3: record no-change as failure
  AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
  AIDER_TASK_MODEL="$ROUTED_MODEL" \
  AIDER_TASK_DURATION="$AIDER_DURATION" \
  python3 - <<'PY'
import os, sys
sys.path.insert(0, ".")
from domains.learning import LearningDomain
LearningDomain().record_execution(
    task_type="coding",
    description=os.environ.get("AIDER_TASK_DESCRIPTION", "")[:120],
    model=os.environ.get("AIDER_TASK_MODEL", "unknown"),
    executor="LOCAL_AIDER",
    success=False,
    duration_seconds=float(os.environ.get("AIDER_TASK_DURATION", "0")),
    error_type="no_changes",
    exit_code=0,
)
print("[aider-task] learning: recorded no-change failure")
PY
else
  echo "[aider-task] Aider modified: ${CHANGED_FILES[*]}"
  echo ""

  # --- Layer 1: Post-run diff sanity check (D-17-103) ---
  GUARD_EXIT=0
  if [[ "$SKIP_VALIDATOR" -eq 0 && "${AIDER_SKIP_VALIDATOR:-0}" != "1" ]]; then
    GUARD_FILES_ARGS=()
    for f in "${CHANGED_FILES[@]}"; do GUARD_FILES_ARGS+=(--files "$f"); done
    set +e
    GUARD_EXTRA_ARGS=()
    [[ $ALLOW_LARGE_INSERTIONS -eq 1 ]] && GUARD_EXTRA_ARGS+=(--allow-large-insertions)
    python3 bin/aider_guard.py \
      --inline \
      --description "$DESCRIPTION" \
      --task-class "${TASK_CLASS:-}" \
      "${GUARD_EXTRA_ARGS[@]}" \
      "${GUARD_FILES_ARGS[@]}"
    GUARD_EXIT=$?
    set -e
  fi

  if [[ $QUIET -eq 1 ]]; then
    for f in "${CHANGED_FILES[@]}"; do
      STAT=$(git diff --shortstat "$f" | sed "s/^ *//")
      echo "[aider-task] modified $f ($STAT)"
    done
  else
    echo "[aider-task] Review the diff:"
    for f in "${CHANGED_FILES[@]}"; do
      git diff "$f"
    done
  fi

  if [[ $GUARD_EXIT -eq 1 ]]; then
    echo ""
    echo "[aider-task] *** DIFF SANITY CHECK FAILED — review diff above before applying ***"
    echo "[aider-task] The diff contains suspicious deletions. Do NOT git add until reviewed."
    echo "[aider-task] If you have reviewed and approve: git add + git commit manually."
    echo "[aider-task] Override next run: --skip-validator or AIDER_SKIP_VALIDATOR=1"
    echo "[aider-task] For large legitimate refactors: --allow-large-insertions"

    # Layer 3: record guarded (operator must decide)
    AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
    AIDER_TASK_MODEL="$ROUTED_MODEL" \
    AIDER_TASK_DURATION="$AIDER_DURATION" \
    python3 - <<'PY'
import os, sys
sys.path.insert(0, ".")
from domains.learning import LearningDomain
LearningDomain().record_execution(
    task_type="coding",
    description=os.environ.get("AIDER_TASK_DESCRIPTION", "")[:120],
    model=os.environ.get("AIDER_TASK_MODEL", "unknown"),
    executor="LOCAL_AIDER",
    success=False,
    duration_seconds=float(os.environ.get("AIDER_TASK_DURATION", "0")),
    error_type="diff_sanity_block",
    exit_code=0,
)
print("[aider-task] learning: recorded diff-sanity-block")
PY
    # Exit 4 = diff sanity block (distinct from Aider errors)
    exit 4
  fi

  # Layer 3: record success
  AIDER_TASK_DESCRIPTION="$DESCRIPTION" \
  AIDER_TASK_MODEL="$ROUTED_MODEL" \
  AIDER_TASK_DURATION="$AIDER_DURATION" \
  python3 - <<'PY'
import os, sys
sys.path.insert(0, ".")
from domains.learning import LearningDomain
LearningDomain().record_execution(
    task_type="coding",
    description=os.environ.get("AIDER_TASK_DESCRIPTION", "")[:120],
    model=os.environ.get("AIDER_TASK_MODEL", "unknown"),
    executor="LOCAL_AIDER",
    success=True,
    duration_seconds=float(os.environ.get("AIDER_TASK_DURATION", "0")),
    exit_code=0,
)
print("[aider-task] learning: recorded success")
PY

  if [[ $AUTO_COMMIT -eq 1 ]]; then
    echo ""
    echo "[aider-task] --commit: staging and committing changes..."
    git add "${CHANGED_FILES[@]}"
    COMMIT_MSG="aider: ${DESCRIPTION:0:72}"
    git commit -m "$COMMIT_MSG"
    COMMIT_HASH=$(git rev-parse --short HEAD)
    echo "[aider-task] Committed: $COMMIT_HASH — $COMMIT_MSG"
  else
    if [[ $QUIET -eq 1 ]]; then
      [[ $GUARD_EXIT -eq 0 ]] && echo "[aider-task] guard=PASS"
      echo "[aider-task] commit: git add ${CHANGED_FILES[*]} && git commit -m \"<msg>\""
    else
      echo ""
      echo "[aider-task] Next steps:"
      echo "  git add ${CHANGED_FILES[*]}"
      echo "  git commit -m \"<your message>\""
      echo ""
      echo "  Aider in-session commands (if session still open):"
      echo "    /diff   show what changed"
      echo "    /undo   revert the last edit"
      echo "    /add <file>  add another file to context"
    fi
  fi
fi
