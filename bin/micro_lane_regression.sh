#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
MSG_DIR="$REPO_ROOT/regressions/micro_lane_stage3/messages"
SUMMARY_DIR="$REPO_ROOT/artifacts/micro_runs"

usage() {
  cat <<'USAGE'
Usage: bin/micro_lane_regression.sh

Runs the Stage 3 fast micro-lane regression pack:
  1. accepted literal wording edit
  2. accepted single-line comment edit
  3. literal-miss rejection
  4. shell-control rejection
  5. aider-exit guard scenario

Requires a clean working tree and leaves the repo clean.
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
      git checkout -- "$file" >/dev/null
      ;;
    failure|guard)
      if [ "$status" -eq 0 ]; then
        echo "ERROR: $label expected failure but succeeded" >&2
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

run_probe "literal wording" "literal_ok.msg" "bin/aider_export_training_jsonl.sh" "success"
run_probe "comment-only" "comment_ok.msg" "bin/detect_changed_files.sh" "success"
run_probe "literal miss" "literal_miss.msg" "bin/aider_local.sh" "failure"
run_probe "shell control" "shell_risky.msg" "bin/aider_local.sh" "failure"
run_probe "aider exit" "guard_banner.msg" "bin/preflight_normalization_guard.sh" "guard"

echo "PASS: Stage 3 micro-lane regression pack completed."
