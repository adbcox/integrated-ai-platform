#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

TASK_NAME=""
GOAL=""
TASK_FILE=""
OFFLINE_MODE="changed"
REMOTE_ENABLED=1
EXPORT_ENABLED=1
PROMPT_ENABLED=1
DRY_RUN=0
HANDOFF_INCLUDES=""
SUMMARY_FILE=""
OUTCOME_FILE=""
CHECKS_FILE=""
WORKFLOW_MODE="${WORKFLOW_MODE:-tactical}"
REMOTE_SET=0
OFFLINE_SET=0

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_loop.sh --name <task-name> [options]

Options:
  --workflow-mode <mode>   tactical|codex-assist|codex-investigate|codex-failure
  --goal <text>            Task objective for auto-generated brief
  --task-file <path>       Use an existing task brief instead of creating one
  --include <path>         Additional include for remote handoff (repeatable)
  --offline <mode>         changed|full|skip (default: changed)
  --no-remote              Skip remote handoff step
  --no-export              Skip training JSONL export step
  --no-prompt              Do not pause for manual patch application
  --summary <path>         Feedback summary file for capture step
  --outcome <path>         Feedback outcome file for capture step
  --checks <path>          Feedback checks file for capture step
  --dry-run                Print actions without executing
  -h, --help               Show help

Default loop:
  1) create or use task brief
  2) prepare remote-safe handoff bundle
  3) pause for patch application
  4) run local finalize checks
  5) capture feedback
  6) export training JSONL
USAGE
}

run_cmd() {
  echo "+ $*"
  if [ "$DRY_RUN" -eq 0 ]; then
    "$@"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workflow-mode)
      WORKFLOW_MODE="${2:-}"
      shift 2
      ;;
    --name)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --goal)
      GOAL="${2:-}"
      shift 2
      ;;
    --task-file)
      TASK_FILE="${2:-}"
      shift 2
      ;;
    --include)
      inc="${2:-}"
      [ -n "$inc" ] || { echo "ERROR: --include requires value" >&2; exit 1; }
      HANDOFF_INCLUDES="$HANDOFF_INCLUDES
$inc"
      shift 2
      ;;
    --offline)
      OFFLINE_MODE="${2:-}"
      OFFLINE_SET=1
      shift 2
      ;;
    --no-remote)
      REMOTE_ENABLED=0
      REMOTE_SET=1
      shift
      ;;
    --no-export)
      EXPORT_ENABLED=0
      shift
      ;;
    --no-prompt)
      PROMPT_ENABLED=0
      shift
      ;;
    --summary)
      SUMMARY_FILE="${2:-}"
      shift 2
      ;;
    --outcome)
      OUTCOME_FILE="${2:-}"
      shift 2
      ;;
    --checks)
      CHECKS_FILE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

[ -n "$TASK_NAME" ] || { echo "ERROR: --name is required" >&2; exit 1; }

case "$WORKFLOW_MODE" in
  tactical|codex-assist|codex-investigate|codex-failure) ;;
  *)
    echo "ERROR: invalid --workflow-mode: $WORKFLOW_MODE" >&2
    exit 1
    ;;
esac

# Mode defaults apply only when operator did not explicitly override flags.
case "$WORKFLOW_MODE" in
  tactical)
    [ "$REMOTE_SET" -eq 1 ] || REMOTE_ENABLED=0
    [ "$OFFLINE_SET" -eq 1 ] || OFFLINE_MODE="changed"
    ;;
  codex-assist)
    [ "$REMOTE_SET" -eq 1 ] || REMOTE_ENABLED=1
    [ "$OFFLINE_SET" -eq 1 ] || OFFLINE_MODE="changed"
    ;;
  codex-investigate|codex-failure)
    [ "$REMOTE_SET" -eq 1 ] || REMOTE_ENABLED=1
    [ "$OFFLINE_SET" -eq 1 ] || OFFLINE_MODE="full"
    ;;
esac

case "$OFFLINE_MODE" in
  changed|full|skip) ;;
  *)
    echo "ERROR: invalid --offline mode: $OFFLINE_MODE" >&2
    exit 1
    ;;
esac

cd "$BASE_DIR"
echo "[aider-loop] workflow mode: $WORKFLOW_MODE"

if [ -z "$TASK_FILE" ]; then
  echo "[aider-loop] Creating task brief..."
  if [ -n "$GOAL" ]; then
    run_cmd ./bin/aider_start_task.sh --name "$TASK_NAME" --goal "$GOAL"
  else
    run_cmd ./bin/aider_start_task.sh --name "$TASK_NAME"
  fi

  slug="$(printf '%s' "$TASK_NAME" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
  [ -n "$slug" ] || slug="task"
  if [ "$DRY_RUN" -eq 0 ]; then
    TASK_FILE="$(ls -1t "$BASE_DIR"/tmp/"$slug"-*.md 2>/dev/null | head -n 1 || true)"
  else
    TASK_FILE="$BASE_DIR/tmp/${slug}-<timestamp>.md"
  fi
fi

if [ -z "$TASK_FILE" ]; then
  echo "ERROR: could not determine task file path" >&2
  exit 1
fi

echo "[aider-loop] Task file: $TASK_FILE"

if [ "$REMOTE_ENABLED" -eq 1 ]; then
  echo "[aider-loop] Preparing remote handoff bundle..."
  set -- ./bin/aider_handoff.sh --task-file "$TASK_FILE" --name "$TASK_NAME"
  while IFS= read -r inc; do
    [ -n "$inc" ] || continue
    set -- "$@" --include "$inc"
  done <<EOF
$HANDOFF_INCLUDES
EOF
  run_cmd "$@"

  if [ "$PROMPT_ENABLED" -eq 1 ]; then
    if [ "$DRY_RUN" -eq 0 ]; then
      echo
      echo "[aider-loop] Apply the remote patch now, then press Enter to continue."
      IFS= read -r _unused
    else
      echo "[aider-loop] DRY-RUN: would pause for manual patch application."
    fi
  fi
else
  echo "[aider-loop] Remote handoff disabled (--no-remote)."
fi

echo "[aider-loop] Running local finalize checks..."
run_cmd ./bin/remote_finalize.sh --offline "$OFFLINE_MODE"

echo "[aider-loop] Capturing feedback record..."
set -- ./bin/aider_capture_feedback.sh --name "$TASK_NAME"
[ -n "$SUMMARY_FILE" ] && set -- "$@" --summary "$SUMMARY_FILE"
[ -n "$OUTCOME_FILE" ] && set -- "$@" --outcome "$OUTCOME_FILE"
[ -n "$CHECKS_FILE" ] && set -- "$@" --checks "$CHECKS_FILE"
run_cmd "$@"

if [ "$EXPORT_ENABLED" -eq 1 ]; then
  echo "[aider-loop] Exporting training JSONL..."
  run_cmd ./bin/aider_export_training_jsonl.sh
else
  echo "[aider-loop] Training export skipped (--no-export)."
fi

echo "PASS: aider loop complete."
