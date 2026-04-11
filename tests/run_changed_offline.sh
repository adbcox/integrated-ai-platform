#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DETECT="$BASE_DIR/bin/detect_changed_files.sh"
RUNNER="$BASE_DIR/tests/run_offline_scenarios.sh"

if [ ! -x "$DETECT" ]; then
  echo "ERROR: missing helper: $DETECT" >&2
  exit 1
fi
if [ ! -x "$RUNNER" ]; then
  echo "ERROR: missing runner: $RUNNER" >&2
  exit 1
fi

changed_files="$("$DETECT" "$@")"
changed_file_list="$(mktemp "${TMPDIR:-/tmp}/changed-offline.files.XXXXXX")"
cleanup() {
  rm -f "$changed_file_list"
}
trap cleanup EXIT INT TERM
printf '%s\n' "$changed_files" >"$changed_file_list"

if [ -z "$changed_files" ]; then
  echo "[changed-offline] No changed files detected; skipping."
  exit 0
fi

run_all=0
need_open_app=0
need_open_and_click=0
need_open_container_target=0

while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    .compat-archive/*|.rename-backups/*|.host-backups/*|*.bak.*|*.bad_*|qnap_*.sh)
      continue
      ;;
  esac
  case "$f" in
    tests/run_offline_scenarios.sh|tests/run_changed_offline.sh|tests/mock_bop.sh|tests/mock_login_flow.sh|tests/scenarios/*|Makefile)
      run_all=1
      ;;
    shell/common.sh|bop.sh)
      run_all=1
      ;;
    browser_operator_open_app.sh|browser_operator_login_flow.sh)
      need_open_app=1
      ;;
    browser_operator_open_and_click.sh)
      need_open_and_click=1
      ;;
    browser_operator_open_container_target.sh)
      need_open_container_target=1
      ;;
  esac
done <"$changed_file_list"

if [ "$run_all" -eq 1 ]; then
  echo "[changed-offline] Running full offline scenario suite..."
  "$RUNNER"
  exit 0
fi

selected_cases=""
if [ "$need_open_app" -eq 1 ]; then
  selected_cases="$selected_cases open-app-deep-loaded open-app-modal-blocked open-app-missing-session"
fi
if [ "$need_open_and_click" -eq 1 ]; then
  selected_cases="$selected_cases open-and-click-hit open-and-click-miss"
fi
if [ "$need_open_container_target" -eq 1 ]; then
  selected_cases="$selected_cases open-container-target-deep-loaded open-container-target-modal-blocked"
fi

selected_cases="$(printf '%s\n' "$selected_cases" | tr ' ' '\n' | sed '/^$/d' | sort -u | tr '\n' ' ')"

if [ -z "$selected_cases" ]; then
  echo "[changed-offline] No relevant browser-operator script changes; skipping."
  exit 0
fi

echo "[changed-offline] Running targeted cases:$selected_cases"
# shellcheck disable=SC2086
"$RUNNER" $selected_cases
