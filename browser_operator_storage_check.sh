#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BOP_BIN="${BOP_BIN:-$BASE/bop.sh}"
QNAP_URL="${QNAP_URL:-https://192.168.10.201/cgi-bin/}"
QNAP_USER="${QNAP_USER:-admin}"
QNAP_PASS="${QNAP_PASS:-*Huckbear17}"
ARTIFACT_NAME="${ARTIFACT_NAME:-browser-operator-storage-check.png}"
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

echo "[1/9] Starting browser session..."
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
echo "[2/9] Opening NAS login page..."
$BOP_BIN open "$SESSION_ID" "$QNAP_URL"

echo
echo "[3/9] Filling username and advancing..."
$BOP_BIN fill-input-index "$SESSION_ID" 0 "$QNAP_USER"
$BOP_BIN click-index "$SESSION_ID" 3

echo
echo "[4/9] Snapshot after username step..."
PASS_SNAPSHOT="$($BOP_BIN dom-snapshot "$SESSION_ID" 2500)"
echo "$PASS_SNAPSHOT"

echo
echo "[5/9] Filling password and logging in..."
$BOP_BIN fill-input-index "$SESSION_ID" 0 "$QNAP_PASS"
$BOP_BIN click-index "$SESSION_ID" 3

echo
echo "[6/9] Waiting for QTS shell to render..."
$BOP_BIN wait "$SESSION_ID" 2500

echo
echo "[7/9] Attempting to dismiss update/notice modal if present..."
CLICKABLE_JSON="$($BOP_BIN list-clickable "$SESSION_ID" 100)"
echo "$CLICKABLE_JSON"

CANCEL_INDEX="$(printf '%s\n' "$CLICKABLE_JSON" | tr '{' '\n' | grep '"label":"Cancel"' | sed -n 's/.*"index":\([0-9][0-9]*\).*/\1/p' | head -1 || true)"
if [ -n "${CANCEL_INDEX:-}" ]; then
  echo "Found Cancel button at index $CANCEL_INDEX; clicking it."
  $BOP_BIN click-index "$SESSION_ID" "$CANCEL_INDEX"
  $BOP_BIN wait "$SESSION_ID" 1500
else
  echo "No Cancel button found; continuing."
fi

echo
echo "[8/9] Opening Storage & Snapshots..."
$BOP_BIN click-text "$SESSION_ID" 'Storage & Snapshots'
$BOP_BIN wait "$SESSION_ID" 2500

echo
echo "[9/9] Reading Storage & Snapshots page and taking screenshot..."
READ_JSON="$($BOP_BIN read "$SESSION_ID" 7000)"
echo "$READ_JSON"
SCREEN_JSON="$($BOP_BIN screenshot "$SESSION_ID" "$ARTIFACT_NAME")"
echo "$SCREEN_JSON"

echo
echo "===== SUMMARY ====="
if printf '%s' "$READ_JSON" | grep -q 'Storage & Snapshots'; then
  echo "Storage & Snapshots page: reached"
else
  echo "Storage & Snapshots page: not clearly confirmed"
fi

if printf '%s' "$READ_JSON" | grep -q 'DataVol1'; then
  echo "Detected volume: DataVol1"
fi

if printf '%s' "$READ_JSON" | grep -q 'Storage Pool'; then
  echo "Detected: Storage Pool section"
fi

if printf '%s' "$READ_JSON" | grep -q 'Disks/VJBOD'; then
  echo "Detected: Disks/VJBOD navigation"
fi

SCREEN_PATH="$(printf '%s' "$SCREEN_JSON" | extract_json_field screenshot_path)"
if [ -n "$SCREEN_PATH" ]; then
  echo "Screenshot: $SCREEN_PATH"
fi

echo "Session: $SESSION_ID"
