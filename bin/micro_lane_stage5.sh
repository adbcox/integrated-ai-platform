#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
BATCH_DIR="$REPO_ROOT/regressions/micro_lane_stage5/batches"
TRACE_SUMMARY="$REPO_ROOT/artifacts/micro_runs/last_summary.txt"

usage() {
  cat <<'USAGE'
Usage: bin/micro_lane_stage5.sh

Runs the Stage-5 boundary pack (success + three guard failures).
Requires a clean working tree; each probe reverts to the starting HEAD.
USAGE
}

ALLOW_DIRTY="${ALLOW_DIRTY:-0}"

ensure_clean_tree() {
  if [ "$ALLOW_DIRTY" -eq 1 ]; then
    return
  fi
  if [ -n "$(git status --short)" ]; then
    echo "ERROR: working tree must be clean before Stage-5 regressions." >&2
    git status --short >&2
    exit 1
  fi
}

run_probe() {
  local label="$1"
  local batch="$2"
  local expect="$3"
  shift 3
  local extra=("$@")

  echo "== [$label] =="
  ensure_clean_tree
  local head_ref
  head_ref="$(git rev-parse --verify HEAD)"

  set +e
  python3 "$REPO_ROOT/bin/stage5_manager.py" \
    --batch-file "$BATCH_DIR/$batch" \
    --commit-msg "stage5-regression-${label// /-}" \
    "${extra[@]}"
  local status=$?
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
    *)
      echo "ERROR: unknown expectation '$expect'" >&2
      exit 1
      ;;
  esac

  git reset --hard "$head_ref" >/dev/null
  ensure_clean_tree

  if [ -f "$TRACE_SUMMARY" ]; then
    tail -n 4 "$TRACE_SUMMARY" || true
  fi
  echo
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ensure_clean_tree

run_probe "dual success" "dual_success.json" "success"
run_probe "stale anchor" "stale_anchor.json" "failure"
run_probe "over budget" "dual_success.json" "failure" --max-total-lines 2
run_probe "unsafe target" "unsafe_target.json" "failure"

echo "PASS: Stage-5 micro-lane boundary pack completed."
