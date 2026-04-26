#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BOP_BIN="${BOP_BIN:-$BASE/bop.sh}"
QNAP_URL="${QNAP_URL:-https://192.168.10.201/cgi-bin/}"
QNAP_USER="${QNAP_USER:-admin}"
QNAP_PASS="${QNAP_PASS:-*Huckbear17}"
COMMON_SH="${COMMON_SH:-$BASE/shell/common.sh}"

if [ ! -r "$COMMON_SH" ]; then
  echo "ERROR: shared shell helpers not found/readable: $COMMON_SH" >&2
  exit 1
fi

. "$COMMON_SH"

require_exec "$BOP_BIN" || exit 1
require_exec sed || exit 1
require_exec grep || exit 1
require_exec tr || exit 1

echo "[1/14] Starting browser session..."
START_JSON="$($BOP_BIN start)"
echo "$START_JSON"
SESSION_ID="$(extract_session_id "$START_JSON" || true)"
if [ -z "$SESSION_ID" ]; then
  echo "Failed to extract session_id from bop start output." >&2
  exit 1
fi

cleanup() {
  echo
  echo "[cleanup] Closing session: $SESSION_ID"
  "$BOP_BIN" close "$SESSION_ID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo
echo "[2/14] Opening QNAP login page..."
$BOP_BIN open "$SESSION_ID" "$QNAP_URL"

echo
echo "[3/14] Filling username and advancing..."
$BOP_BIN fill-input-index "$SESSION_ID" 0 "$QNAP_USER"
$BOP_BIN click-index "$SESSION_ID" 3

echo
echo "[4/14] Filling password and logging in..."
$BOP_BIN fill-input-index "$SESSION_ID" 0 "$QNAP_PASS"
$BOP_BIN click-index "$SESSION_ID" 3
$BOP_BIN wait "$SESSION_ID" 2500

echo
echo "[5/14] Waiting for desktop shell..."
$BOP_BIN read "$SESSION_ID" 3000 || true
$BOP_BIN wait "$SESSION_ID" 1500

echo
echo "[6/14] Dismissing modal if Cancel is present..."
CLICKABLE_JSON="$($BOP_BIN list-clickable "$SESSION_ID" 100)"
echo "$CLICKABLE_JSON"

CANCEL_INDEX="$(printf '%s\n' "$CLICKABLE_JSON" | tr '{' '\n' | grep '"label":"Cancel"' | sed -n 's/.*"index":\([0-9][0-9]*\).*/\1/p' | head -1 || true)"
if [ -n "${CANCEL_INDEX:-}" ]; then
  echo "Found Cancel button at index $CANCEL_INDEX; clicking it."
  $BOP_BIN click-index "$SESSION_ID" "$CANCEL_INDEX" || true
  $BOP_BIN wait "$SESSION_ID" 1500
else
  echo "No Cancel button found at this stage."
fi

echo
echo "[7/14] Opening Storage & Snapshots (normal click, then JS fallback)..."
$BOP_BIN click-text "$SESSION_ID" 'Storage & Snapshots' || true
$BOP_BIN wait "$SESSION_ID" 2500
READ_STORAGE="$($BOP_BIN read "$SESSION_ID" 7000)"
echo "$READ_STORAGE"

if ! printf '%s' "$READ_STORAGE" | grep -q 'System - Enclosure:'; then
  echo "Normal click did not clearly reach storage details; trying JS click..."
  $BOP_BIN click-js-text "$SESSION_ID" 'Storage & Snapshots'
  $BOP_BIN wait "$SESSION_ID" 3000
  READ_STORAGE="$($BOP_BIN read "$SESSION_ID" 7000)"
  echo "$READ_STORAGE"
fi

$BOP_BIN screenshot "$SESSION_ID" browser-operator-disks-vjbod-overview.png >/dev/null || true

echo
echo "[8/14] Opening Disks/VJBOD (normal click, then JS fallback)..."
$BOP_BIN click-text "$SESSION_ID" 'Disks/VJBOD' || true
$BOP_BIN wait "$SESSION_ID" 3000
READ_DISKS="$($BOP_BIN read "$SESSION_ID" 9000)"
echo "$READ_DISKS"

if ! printf '%s' "$READ_DISKS" | grep -q 'Manufacturer:'; then
  echo "Normal click did not clearly reach disk details; trying JS click..."
  $BOP_BIN click-js-text "$SESSION_ID" 'Disks/VJBOD'
  $BOP_BIN wait "$SESSION_ID" 3000
  READ_DISKS="$($BOP_BIN read "$SESSION_ID" 9000)"
  echo "$READ_DISKS"
fi

$BOP_BIN screenshot "$SESSION_ID" browser-operator-disks-vjbod-overview.png >/dev/null || true

echo
echo "[9/14] DOM snapshot for disk links..."
SNAP_JSON="$($BOP_BIN dom-snapshot "$SESSION_ID" 9000)"
echo "$SNAP_JSON"

echo
echo "[10/14] Clickable elements for disk links..."
CLICK_JSON="$($BOP_BIN list-clickable "$SESSION_ID" 100)"
echo "$CLICK_JSON"

echo
echo "[11/14] Clicking exposed disk links if present..."
for IDX in 12 13 14 15; do
  echo
  echo "[disk] Trying click-index-js on disk item $IDX..."
  if $BOP_BIN click-index-js "$SESSION_ID" "$IDX" >/tmp/browser_operator_disk_click.out 2>/tmp/browser_operator_disk_click.err; then
    cat /tmp/browser_operator_disk_click.out
    $BOP_BIN wait "$SESSION_ID" 2500
    DISK_READ="$($BOP_BIN read "$SESSION_ID" 7000)"
    echo "$DISK_READ"
    case "$IDX" in
      12) NAME="disk1" ;;
      13) NAME="disk2" ;;
      14) NAME="disk3" ;;
      15) NAME="disk4" ;;
      *) NAME="disk$IDX" ;;
    esac
    $BOP_BIN screenshot "$SESSION_ID" "${NAME}-health.png" >/dev/null || true
  else
    echo "Disk item $IDX not clickable via JS."
    cat /tmp/browser_operator_disk_click.err || true
  fi
done

echo
echo "[12/14] Final disk detail read..."
FINAL_READ="$($BOP_BIN read "$SESSION_ID" 9000)"
echo "$FINAL_READ"

echo
echo "[13/14] Final clickables snapshot..."
FINAL_CLICK_JSON="$($BOP_BIN list-clickable "$SESSION_ID" 100)"
echo "$FINAL_CLICK_JSON"

echo
echo "[14/14] Summary markers..."
echo "===== SUMMARY ====="

if printf '%s' "$FINAL_READ" | grep -q 'Disks/VJBOD'; then
  echo "Disks/VJBOD page: reached"
elif printf '%s' "$FINAL_READ" | grep -q '3.5\" SATA HDD 1'; then
  echo "Disks/VJBOD page: effectively reached via disk links"
else
  echo "Disks/VJBOD page: not clearly confirmed"
fi

if printf '%s' "$FINAL_READ" | grep -q 'Manufacturer:'; then
  echo "Detected: Manufacturer field"
fi

if printf '%s' "$FINAL_READ" | grep -q 'Model:'; then
  echo "Detected: Model field"
fi

if printf '%s' "$FINAL_READ" | grep -q 'Status:'; then
  echo "Detected: Status field"
fi

if printf '%s' "$FINAL_READ" | grep -q 'Temperature:'; then
  echo "Detected: Temperature field"
fi

if printf '%s' "$FINAL_READ" | grep -q 'Good'; then
  echo "Detected health marker: Good"
fi

if printf '%s' "$FINAL_CLICK_JSON" | grep -q '3.5\\" SATA HDD 1'; then
  echo "Detected clickable disk entries"
fi

echo "Artifacts:"
echo "  artifacts/browser-operator-disks-vjbod-overview.png"
echo "  artifacts/disk1-health.png"
echo "  artifacts/disk2-health.png"
echo "  artifacts/disk3-health.png"
echo "  artifacts/disk4-health.png"
echo "Session: $SESSION_ID"
