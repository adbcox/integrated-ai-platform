#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
PLAN_DIR="$REPO_ROOT/artifacts/manager5/plans"

usage() {
  cat <<'USAGE'
Usage: bin/micro_lane_stage6.sh

Runs Stage-6 preview orchestration regression probes:
  1. basic dry-run plan lifecycle
  2. confidence gate -> no eligible targets
  3. confidence gate + allowed fallback target
  4. confidence gate + disallowed fallback target (expected failure)

Requires a clean working tree and leaves the repository clean.
USAGE
}

ensure_clean_tree() {
  if [ -n "$(git status --short)" ]; then
    echo "ERROR: working tree must be clean before Stage-6 regressions." >&2
    git status --short >&2
    exit 1
  fi
}

assert_plan_state() {
  local plan_path="$1"
  local expected_state="$2"
  python3 - "$plan_path" "$expected_state" <<'PY'
import json
import sys
plan_path, expected = sys.argv[1], sys.argv[2]
payload = json.loads(open(plan_path, encoding="utf-8").read())
state = payload.get("current_state")
if state != expected:
    raise SystemExit(f"expected state={expected!r}, got {state!r}")
print(f"state={state}")
PY
}

run_probe() {
  local label="$1"
  local expected="$2"
  shift 2
  local plan_id="stage6-reg-$(date -u +%Y%m%d%H%M%S)-$RANDOM"
  local plan_path="$PLAN_DIR/${plan_id}.json"

  echo "== [$label] =="
  ensure_clean_tree

  set +e
  python3 "$REPO_ROOT/bin/stage6_manager.py" \
    --query "stage6 placeholder literal" \
    --plan-id "$plan_id" \
    --commit-msg "stage6-regression-$label" \
    "$@"
  local status=$?
  set -e

  if [ "$expected" = "success" ] && [ "$status" -ne 0 ]; then
    echo "ERROR: $label expected success but exited $status" >&2
    exit 1
  fi
  if [ "$expected" = "failure" ] && [ "$status" -eq 0 ]; then
    echo "ERROR: $label expected failure but succeeded" >&2
    exit 1
  fi

  if [ "$expected" = "success" ] && [ ! -f "$plan_path" ]; then
    echo "ERROR: $label expected plan file at $plan_path" >&2
    exit 1
  fi

  if [ "$expected" = "failure" ] && [ -f "$plan_path" ]; then
    echo "NOTE: failure probe produced plan file $plan_path"
  fi

  ensure_clean_tree
  echo
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

ensure_clean_tree

run_probe "basic-dryrun-live" "success" --dry-run --max-entries 2
latest_basic_plan="$(ls -1t "$PLAN_DIR"/stage6-reg-*.json | head -n 1)"
assert_plan_state "$latest_basic_plan" "succeeded"

run_probe "confidence-empty" "success" --dry-run --max-entries 2 --min-confidence 99
latest_empty_plan="$(ls -1t "$PLAN_DIR"/stage6-reg-*.json | head -n 1)"
assert_plan_state "$latest_empty_plan" "no_eligible_targets"

run_probe "fallback-allowed" "success" --dry-run --max-entries 2 --min-confidence 99 --fallback-target "bin/stage6_manager.py"
latest_fallback_plan="$(ls -1t "$PLAN_DIR"/stage6-reg-*.json | head -n 1)"
assert_plan_state "$latest_fallback_plan" "succeeded"

run_probe "fallback-disallowed" "failure" --dry-run --max-entries 2 --min-confidence 99 --fallback-target "docs/stage6-preview.md"

echo "PASS: Stage-6 micro-lane regression pack completed."
