#!/bin/sh
set -eu

BASE_DIR="${BASE_DIR:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"

OPEN_APP_SCRIPT="${OPEN_APP_SCRIPT:-$BASE_DIR/browser_operator_open_app.sh}"
OPEN_AND_CLICK_SCRIPT="${OPEN_AND_CLICK_SCRIPT:-$BASE_DIR/browser_operator_open_and_click.sh}"

if [ ! -x "$OPEN_APP_SCRIPT" ]; then
  echo "Missing executable: $OPEN_APP_SCRIPT" >&2
  exit 1
fi

if [ ! -x "$OPEN_AND_CLICK_SCRIPT" ]; then
  echo "Missing executable: $OPEN_AND_CLICK_SCRIPT" >&2
  exit 1
fi

run_task() {
  echo
  echo "============================================================"
  echo "TASK: $*"
  echo "============================================================"
  "$@"
}

echo "[1/4] Running Storage -> Disks/VJBOD workflow..."
run_task "$OPEN_AND_CLICK_SCRIPT" 'Storage & Snapshots' 'Disks/VJBOD'

echo
echo "[2/4] Running Container Station open workflow..."
run_task "$OPEN_APP_SCRIPT" 'Container Station'

echo
echo "[3/4] Running App Center open workflow..."
run_task "$OPEN_APP_SCRIPT" 'App Center'

echo
echo "[4/4] Batch complete."
echo "Artifacts available under: $BASE_DIR/artifacts"
