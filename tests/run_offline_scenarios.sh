#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TEST_DIR="$BASE_DIR/tests"
SCENARIO_DIR="$TEST_DIR/scenarios"
MOCK_BOP="$TEST_DIR/mock_bop.sh"
MOCK_LOGIN="$TEST_DIR/mock_login_flow.sh"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/browser-operator-offline.XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

require_file() {
  path="$1"
  if [ ! -r "$path" ]; then
    echo "ERROR: required file not found/readable: $path" >&2
    exit 1
  fi
}

require_file "$MOCK_BOP"
require_file "$MOCK_LOGIN"
require_file "$SCENARIO_DIR/deep_loaded.env"
require_file "$SCENARIO_DIR/modal_blocked.env"
require_file "$SCENARIO_DIR/missing_session.env"
require_file "$SCENARIO_DIR/open_and_click_hit.env"
require_file "$SCENARIO_DIR/open_and_click_miss.env"

CASE_FILTER="${*:-}"

should_run_case() {
  case_name="$1"
  if [ -z "$CASE_FILTER" ]; then
    return 0
  fi

  for requested in $CASE_FILTER; do
    if [ "$requested" = "$case_name" ]; then
      return 0
    fi
  done
  return 1
}

run_case() {
  name="$1"
  expected_exit="$2"
  must_contain="$3"
  must_contain_2="$4"
  scenario_file="$5"
  shift 5

  case_dir="$TMP_DIR/$name"
  mkdir -p "$case_dir/artifacts" "$case_dir/state"
  output_file="$case_dir/output.log"

  echo
  echo "=== CASE: $name ==="
  echo "scenario: $scenario_file"

  set +e
  env \
    SCENARIO_FILE="$scenario_file" \
    MOCK_BOP_STATE_DIR="$case_dir/state" \
    BOP="$MOCK_BOP" \
    LOGIN_FLOW="$MOCK_LOGIN" \
    ARTIFACT_DIR="$case_dir/artifacts" \
    "$@" >"$output_file" 2>&1
  status=$?
  set -e

  echo "exit: $status (expected: $expected_exit)"
  if [ "$status" -ne "$expected_exit" ]; then
    echo "ERROR: unexpected exit code for case '$name'" >&2
    echo "--- output ---" >&2
    cat "$output_file" >&2
    exit 1
  fi

  if ! grep -F "$must_contain" "$output_file" >/dev/null 2>&1; then
    echo "ERROR: expected marker not found for case '$name': $must_contain" >&2
    echo "--- output ---" >&2
    cat "$output_file" >&2
    exit 1
  fi
  echo "OK: marker '$must_contain'"

  if [ "$must_contain_2" != "-" ]; then
    if ! grep -F "$must_contain_2" "$output_file" >/dev/null 2>&1; then
      echo "ERROR: expected marker not found for case '$name': $must_contain_2" >&2
      echo "--- output ---" >&2
      cat "$output_file" >&2
      exit 1
    fi
    echo "OK: marker '$must_contain_2'"
  fi
}

echo "[offline-tests] Running scenario suite..."

if should_run_case "open-app-deep-loaded"; then
run_case \
  "open-app-deep-loaded" \
  0 \
  "PASS" \
  "-" \
  "$SCENARIO_DIR/deep_loaded.env" \
  "$BASE_DIR/browser_operator_open_app.sh" \
  "Container Station"
fi

if should_run_case "open-app-modal-blocked"; then
run_case \
  "open-app-modal-blocked" \
  2 \
  "BLOCKED" \
  "-" \
  "$SCENARIO_DIR/modal_blocked.env" \
  "$BASE_DIR/browser_operator_open_app.sh" \
  "Container Station"
fi

if should_run_case "open-app-missing-session"; then
run_case \
  "open-app-missing-session" \
  1 \
  "Failed to obtain session id." \
  "-" \
  "$SCENARIO_DIR/missing_session.env" \
  "$BASE_DIR/browser_operator_open_app.sh" \
  "Container Station"
fi

if should_run_case "open-and-click-hit"; then
run_case \
  "open-and-click-hit" \
  0 \
  "App target present after navigation: yes" \
  "Follow-up target present after navigation: yes" \
  "$SCENARIO_DIR/open_and_click_hit.env" \
  "$BASE_DIR/browser_operator_open_and_click.sh" \
  "Storage & Snapshots" \
  "Disks/VJBOD"
fi

if should_run_case "open-and-click-miss"; then
run_case \
  "open-and-click-miss" \
  0 \
  "App target present after navigation: yes" \
  "Follow-up target present after navigation: no" \
  "$SCENARIO_DIR/open_and_click_miss.env" \
  "$BASE_DIR/browser_operator_open_and_click.sh" \
  "Storage & Snapshots" \
  "Disks/VJBOD"
fi

if should_run_case "open-container-target-deep-loaded"; then
run_case \
  "open-container-target-deep-loaded" \
  0 \
  "PASS" \
  "-" \
  "$SCENARIO_DIR/deep_loaded.env" \
  "$BASE_DIR/browser_operator_open_container_target.sh"
fi

if should_run_case "open-container-target-modal-blocked"; then
run_case \
  "open-container-target-modal-blocked" \
  2 \
  "BLOCKED" \
  "-" \
  "$SCENARIO_DIR/modal_blocked.env" \
  "$BASE_DIR/browser_operator_open_container_target.sh"
fi

echo
echo "PASS: offline scenario suite complete."
