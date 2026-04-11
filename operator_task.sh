#!/bin/sh
set -eu

BASE_DIR="${BASE_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
OPEN_APP="${BASE_DIR}/browser_operator_open_app.sh"
OPEN_AND_CLICK="${BASE_DIR}/browser_operator_open_and_click.sh"
OPEN_CONTAINER_TARGET="${BASE_DIR}/browser_operator_open_container_target.sh"

usage() {
  cat <<'USAGE'
Usage:
  ./operator_task.sh preset <name>
  ./operator_task.sh open-app "<app name>"
  ./operator_task.sh open-and-click "<app name>" "<target name>"
  ./operator_task.sh run-file <task file>

Supported presets:
  storage-disks
  open-container
  open-app-center

Task file format:
  - blank lines are ignored
  - lines beginning with # are ignored
  - supported commands:

      preset storage-disks
      preset open-container
      preset open-app-center

      open-app "Container Station"
      open-app "App Center"

      open-and-click "Storage & Snapshots" "Disks/VJBOD"

Example:
  ./operator_task.sh run-file "$BASE_DIR/tasks.conf"
USAGE
}

require_file() {
  f="$1"
  if [ ! -x "$f" ]; then
    echo "Required executable not found: $f" >&2
    exit 1
  fi
}

run_preset() {
  preset_name="$1"

  case "$preset_name" in
    storage-disks)
      echo
      echo "============================================================"
      echo "TASK: storage-disks"
      echo "============================================================"
      "$OPEN_AND_CLICK" "Storage & Snapshots" "Disks/VJBOD"
      ;;
    open-container)
      echo
      echo "============================================================"
      echo "TASK: open-container"
      echo "============================================================"
      "$OPEN_APP" "Container Station"
      ;;
    open-container-target)
      echo
      echo "=================================================="
      echo "TASK: open-container-target"
      echo "=================================================="
      "$OPEN_CONTAINER_TARGET"
      ;;
    open-app-center)
      echo
      echo "============================================================"
      echo "TASK: open-app-center"
      echo "============================================================"
      "$OPEN_APP" "App Center"
      ;;
    *)
      echo "Unknown preset: $preset_name" >&2
      exit 1
      ;;
  esac
}

run_open_app() {
  app_name="$1"
  echo
  echo "============================================================"
  echo "TASK: open-app \"$app_name\""
  echo "============================================================"
  "$OPEN_APP" "$app_name"
}

run_open_and_click() {
  app_name="$1"
  target_name="$2"
  echo
  echo "============================================================"
  echo "TASK: open-and-click \"$app_name\" \"$target_name\""
  echo "============================================================"
  "$OPEN_AND_CLICK" "$app_name" "$target_name"
}

run_file() {
  task_file="$1"

  if [ ! -f "$task_file" ]; then
    echo "Task file not found: $task_file" >&2
    exit 1
  fi

  echo "[run-file] Using task file: $task_file"

  line_no=0
  task_no=0

  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    line_no=$((line_no + 1))
    line="$(printf '%s' "$raw_line" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"

    if [ -z "$line" ]; then
      continue
    fi

    case "$line" in
      \#*)
        continue
        ;;
    esac

    task_no=$((task_no + 1))
    echo
    echo "[run-file] Task $task_no from line $line_no: $line"

    case "$line" in
      preset\ *)
        preset_name="${line#preset }"
        run_preset "$preset_name"
        ;;
      open-app\ *)
        app_name="$(printf '%s\n' "$line" | sed -n 's/^open-app "\(.*\)"$/\1/p')"
        if [ -z "$app_name" ]; then
          echo "Invalid open-app syntax at line $line_no: $line" >&2
          exit 1
        fi
        run_open_app "$app_name"
        ;;
      open-and-click\ *)
        parsed="$(printf '%s\n' "$line" | sed -n 's/^open-and-click "\(.*\)" "\(.*\)"$/\1\t\2/p')"
        if [ -z "$parsed" ]; then
          echo "Invalid open-and-click syntax at line $line_no: $line" >&2
          exit 1
        fi
        app_name="$(printf '%s' "$parsed" | cut -f1)"
        target_name="$(printf '%s' "$parsed" | cut -f2)"
        run_open_and_click "$app_name" "$target_name"
        ;;
      *)
        echo "Unknown command at line $line_no: $line" >&2
        exit 1
        ;;
    esac
  done < "$task_file"

  echo
  echo "[run-file] Complete. Tasks executed: $task_no"
}

require_file "$OPEN_APP"
require_file "$OPEN_AND_CLICK"

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

cmd="$1"
shift || true

case "$cmd" in
  preset)
    [ $# -eq 1 ] || { usage; exit 1; }
    run_preset "$1"
    ;;
  open-app)
    [ $# -eq 1 ] || { usage; exit 1; }
    run_open_app "$1"
    ;;
  open-and-click)
    [ $# -eq 2 ] || { usage; exit 1; }
    run_open_and_click "$1" "$2"
    ;;
  run-file)
    [ $# -eq 1 ] || { usage; exit 1; }
    run_file "$1"
    ;;
  *)
    usage
    exit 1
    ;;
esac
