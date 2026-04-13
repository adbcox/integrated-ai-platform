#!/usr/bin/env bash
set -euo pipefail

LINES=${MICRO_CONTEXT_LINES:-80}
declare -a FILES=()
SHOW_CHANGED=1

usage() {
  cat <<'USAGE'
Usage: bin/micro_repo_context.sh [--lines N] [--no-changed] [file ...]

Prints a lightweight repo-aware context summary for planning Stage 3 micro tasks.
- Lists current git status (unless --no-changed is provided)
- Shows the first N lines (default: 80) of each requested file with line numbers
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --lines)
      LINES="${2:-}"
      shift 2
      ;;
    --no-changed)
      SHOW_CHANGED=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

if [ ${#FILES[@]} -eq 0 ]; then
  echo "ERROR: specify at least one file" >&2
  usage
  exit 1
fi

if [ "$SHOW_CHANGED" -eq 1 ]; then
  echo "--- git status (short) ---"
  git status --short || true
  echo
fi

for path in "${FILES[@]}"; do
  if [ ! -f "$path" ]; then
    echo "WARN: skipping missing file $path" >&2
    continue
  fi
  echo "=== $path (first $LINES lines) ==="
  nl -ba "$path" | sed -n "1,${LINES}p"
  echo
fi
