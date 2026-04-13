#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
MSG_DIR="$REPO_ROOT/regressions/micro_lane_stage4/messages"
SUMMARY_DIR="$REPO_ROOT/artifacts/micro_runs"

usage() {
  cat <<'USAGE'
Usage: bin/micro_lane_stage4.sh

Stage 4 boundary probes:
  1. literal3_guard.msg   -> expect aider_exit/guard (current boundary)
  2. comment2_ok.msg      -> expect accepted comment edit
  3. literal_miss.msg     -> expect literal_replace_missing_old
  4. shell_risky.msg      -> expect literal_shell_risky

Requires a clean working tree; leaves repo clean.
USAGE
}

ensure_clean_tree() {
  if [ -n "$(git status --short)" ]; then
    echo "ERROR: working tree must be clean before regressions." >&2
    git status --short
    exit 1
  fi
}

run_probe() {
  local label="$1"
  local msg="$2"
  local file="$3"
  local expect="$4"

  echo "== [$label] =="

  local head_ref
  head_ref="$(git rev-parse --verify HEAD)"

  local status=0
  set +e
  make aider-micro-safe \
    AIDER_MICRO_MESSAGE_FILE="${MSG_DIR}/${msg}" \
    AIDER_MICRO_FILES="${file}"
  status=$?
  set -e

  case "$expect" in
    success)
      if [ "$status" -ne 0 ]; then
        echo "ERROR: $label expected success but exited $status" >&2
        exit 1
      fi
      ;;
    failure)
      if [ "$status" -eq 0 ]; then
        echo "ERROR: $label expected failure but succeeded" >&2
        exit 1
      fi
      ;;
    guard)
      if [ "$status" -eq 0 ]; then
        echo "ERROR: $label expected guard failure but succeeded" >&2
        exit 1
      fi
      ;;
    *)
      echo "ERROR: unknown expectation '$expect'" >&2
      exit 1
      ;;
  esac

  git reset --hard "$head_ref" >/dev/null
  ensure_clean_tree

  if [ -f "$SUMMARY_DIR/last_summary.txt" ]; then
    tail -n 6 "$SUMMARY_DIR/last_summary.txt"
  fi
  echo
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ensure_clean_tree

run_probe "literal three-line" "literal3_guard.msg" "bin/aider_loop.sh" "guard"
run_probe "comment pair" "comment2_ok.msg" "bin/detect_changed_files.sh" "success"
run_probe "literal miss" "literal_miss.msg" "bin/aider_loop.sh" "failure"
run_probe "shell control" "shell_risky.msg" "bin/aider_local.sh" "failure"

echo "PASS: Stage 4 micro-lane boundary pack completed."
