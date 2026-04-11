#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TEMPLATE="$BASE_DIR/templates/aider-task-template.md"
OUT_DIR="$BASE_DIR/tmp"
TASK_NAME=""
GOAL=""
OUT_FILE=""

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_start_task.sh --name <task-name> [--goal <text>] [--out-file <path>]

Creates a task brief from templates/aider-task-template.md.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --goal)
      GOAL="${2:-}"
      shift 2
      ;;
    --out-file)
      OUT_FILE="${2:-}"
      shift 2
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

[ -r "$TEMPLATE" ] || { echo "ERROR: missing template: $TEMPLATE" >&2; exit 1; }
[ -n "$TASK_NAME" ] || { echo "ERROR: --name is required" >&2; exit 1; }

slug="$(printf '%s' "$TASK_NAME" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
[ -n "$slug" ] || slug="task"

if [ -z "$OUT_FILE" ]; then
  mkdir -p "$OUT_DIR"
  OUT_FILE="$OUT_DIR/${slug}-$(date +%Y%m%d_%H%M%S).md"
fi

cp "$TEMPLATE" "$OUT_FILE"

tmpfile="$(mktemp "${TMPDIR:-/tmp}/aider-task.XXXXXX")"
trap 'rm -f "$tmpfile"' EXIT INT TERM

sed "s#<short-name>#$TASK_NAME#g" "$OUT_FILE" >"$tmpfile"
mv "$tmpfile" "$OUT_FILE"

if [ -n "$GOAL" ]; then
  tmpfile2="$(mktemp "${TMPDIR:-/tmp}/aider-task.XXXXXX")"
  trap 'rm -f "$tmpfile" "$tmpfile2"' EXIT INT TERM
  sed "s#<what to change>#$GOAL#g" "$OUT_FILE" >"$tmpfile2"
  mv "$tmpfile2" "$OUT_FILE"
fi

echo "Created task brief: $OUT_FILE"
