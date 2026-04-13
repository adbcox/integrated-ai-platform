#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
REMOTE_PREP="$BASE_DIR/bin/remote_prepare.sh"
DETECT="$BASE_DIR/bin/detect_changed_files.sh"

TASK_FILE=""
TASK_NAME="aider-handoff"
OUT_DIR="$BASE_DIR/.remote-tasks"
INCLUDES=""
AUTO_INCLUDE=1

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_handoff.sh --task-file <path> [--name <task>] [--out-dir <path>] [--include <path> ...] [--no-auto-include]

Behavior:
  - If no --include is provided, auto-includes changed files plus AGENTS.md and docs/validation-matrix.md by default.
  - Produces a remote-safe bundle using bin/remote_prepare.sh.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --task-file)
      TASK_FILE="${2:-}"
      shift 2
      ;;
    --name)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --include)
      item="${2:-}"
      [ -n "$item" ] || { echo "ERROR: --include requires a value" >&2; exit 1; }
      INCLUDES="$INCLUDES
$item"
      shift 2
      ;;
    --no-auto-include)
      AUTO_INCLUDE=0
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

[ -x "$REMOTE_PREP" ] || { echo "ERROR: missing helper: $REMOTE_PREP" >&2; exit 1; }
[ -x "$DETECT" ] || { echo "ERROR: missing helper: $DETECT" >&2; exit 1; }
[ -n "$TASK_FILE" ] || { echo "ERROR: --task-file is required" >&2; exit 1; }
[ -f "$TASK_FILE" ] || { echo "ERROR: task file not found: $TASK_FILE" >&2; exit 1; }

if [ "$AUTO_INCLUDE" -eq 1 ]; then
  changed="$("$DETECT")"
  if [ -n "$changed" ]; then
    INCLUDES="$INCLUDES
$changed"
  fi
  INCLUDES="$INCLUDES
AGENTS.md
docs/validation-matrix.md
docs/remote-codex-workflow.md"
fi

INCLUDES="$(printf '%s\n' "$INCLUDES" | sed '/^$/d' | sort -u)"
[ -n "$INCLUDES" ] || { echo "ERROR: no files selected for handoff" >&2; exit 1; }

set -- "$REMOTE_PREP" --task-file "$TASK_FILE" --out-dir "$OUT_DIR" --name "$TASK_NAME"
while IFS= read -r inc; do
  [ -n "$inc" ] || continue
  set -- "$@" --include "$inc"
done <<EOF
$INCLUDES
EOF

"$@"
