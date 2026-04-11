#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DETECT="$BASE_DIR/bin/detect_changed_files.sh"
OUT_ROOT="$BASE_DIR/.local-model-data"
TASK_NAME=""
SUMMARY_FILE=""
OUTCOME_FILE=""
CHECKS_FILE=""

usage() {
  cat <<'USAGE'
Usage:
  ./bin/aider_capture_feedback.sh --name <task-name> [--summary <path>] [--outcome <path>] [--checks <path>]

Creates a local training feedback record in .local-model-data/.
This is local-only metadata for improving future local model tuning datasets.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name)
      TASK_NAME="${2:-}"
      shift 2
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

[ -x "$DETECT" ] || { echo "ERROR: missing helper: $DETECT" >&2; exit 1; }
[ -n "$TASK_NAME" ] || { echo "ERROR: --name is required" >&2; exit 1; }

slug="$(printf '%s' "$TASK_NAME" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
[ -n "$slug" ] || slug="task"
record_dir="$OUT_ROOT/$(date +%Y%m%d_%H%M%S)_$slug"
mkdir -p "$record_dir"

{
  echo "task_name: $TASK_NAME"
  echo "created_utc: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "repo: $BASE_DIR"
} >"$record_dir/meta.txt"

changed_files="$("$DETECT" | sed '/^$/d' | sort -u)"
printf '%s\n' "$changed_files" >"$record_dir/changed_files.txt"

if [ -n "$SUMMARY_FILE" ] && [ -f "$SUMMARY_FILE" ]; then
  cp "$SUMMARY_FILE" "$record_dir/summary.md"
else
  cat >"$record_dir/summary.md" <<'EOF'
# Summary
<what was changed and why>
EOF
fi

if [ -n "$OUTCOME_FILE" ] && [ -f "$OUTCOME_FILE" ]; then
  cp "$OUTCOME_FILE" "$record_dir/outcome.md"
else
  cat >"$record_dir/outcome.md" <<'EOF'
# Outcome
- status: <pass|partial|fail>
- key regressions prevented:
  - <item>
- follow-ups:
  - <item>
EOF
fi

if [ -n "$CHECKS_FILE" ] && [ -f "$CHECKS_FILE" ]; then
  cp "$CHECKS_FILE" "$record_dir/checks.txt"
else
  cat >"$record_dir/checks.txt" <<'EOF'
make quick
make test-changed-offline
EOF
fi

echo "Captured feedback record: $record_dir"
