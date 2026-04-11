#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BOP="${BOP:-$BASE/bop.sh}"
LOGIN_FLOW="${LOGIN_FLOW:-$BASE/browser_operator_login_flow.sh}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$BASE/artifacts}"
COMMON_SH="${COMMON_SH:-$BASE/shell/common.sh}"

if [ ! -r "$COMMON_SH" ]; then
  echo "ERROR: shared shell helpers not found/readable: $COMMON_SH" >&2
  exit 1
fi

. "$COMMON_SH"

if [ ! -x "$BOP" ]; then
  echo "ERROR: bop not found or not executable: $BOP" >&2
  exit 1
fi

if [ ! -x "$LOGIN_FLOW" ]; then
  echo "ERROR: login flow not found or not executable: $LOGIN_FLOW" >&2
  exit 1
fi

APP_NAME="${1:?app name required}"
TARGET_NAME="${2:?target name required}"

mkdir -p "$ARTIFACT_DIR"

safe_name() {
  printf '%s' "$1" | tr ' /' '__' | tr -cd '[:alnum:]_.-'
}

need_text() {
  needle="$1"
  haystack="$2"
  printf '%s' "$haystack" | grep -F "$needle" >/dev/null 2>&1
}

echo "[1/14] Running shared login flow..."
LOGIN_OUT="$($LOGIN_FLOW 2>&1 || true)"
printf '%s\n' "$LOGIN_OUT"

SESSION_ID="$(extract_session_id "$LOGIN_OUT" || true)"
if [ -z "$SESSION_ID" ]; then
  echo "ERROR: failed to obtain session id from login flow output" >&2
  exit 1
fi

echo "Using session: $SESSION_ID"

cleanup() {
  echo
  echo "[cleanup] Closing session: $SESSION_ID"
  "$BOP" close "$SESSION_ID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo
echo "[2/14] Reading initial desktop state..."
INITIAL_READ="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$INITIAL_READ"

echo
echo "[3/14] Opening app: $APP_NAME"
"$BOP" click-text "$SESSION_ID" "$APP_NAME" || true
"$BOP" wait "$SESSION_ID" 2500 >/dev/null || true
APP_READ_NORMAL="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$APP_READ_NORMAL"

echo
echo "[4/14] JS fallback for app: $APP_NAME"
"$BOP" click-js-text "$SESSION_ID" "$APP_NAME" || true
"$BOP" wait "$SESSION_ID" 3000 >/dev/null || true
APP_READ_JS="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$APP_READ_JS"

echo
echo "[5/14] Clearing modal buttons..."
"$BOP" click-text "$SESSION_ID" "OK" >/dev/null 2>&1 || true
"$BOP" wait "$SESSION_ID" 1200 >/dev/null || true
"$BOP" click-text "$SESSION_ID" "Cancel" >/dev/null 2>&1 || true
"$BOP" wait "$SESSION_ID" 1200 >/dev/null || true
AFTER_MODAL_CLEAR="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$AFTER_MODAL_CLEAR"

echo
echo "[6/14] Re-open app after modal clear..."
"$BOP" click-js-text "$SESSION_ID" "$APP_NAME" >/dev/null 2>&1 || true
"$BOP" wait "$SESSION_ID" 2500 >/dev/null || true
APP_READ_REOPEN="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$APP_READ_REOPEN"

echo
echo "[7/14] Capture DOM before target..."
PRE_TARGET_DOM="$($BOP dom-snapshot "$SESSION_ID" || true)"
printf '%s\n' "$PRE_TARGET_DOM"

echo
echo "[8/14] Attempting target click by text: $TARGET_NAME"
"$BOP" click-text "$SESSION_ID" "$TARGET_NAME" || true
"$BOP" wait "$SESSION_ID" 2500 >/dev/null || true
TARGET_READ_NORMAL="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$TARGET_READ_NORMAL"

echo
echo "[9/14] Attempting target JS click: $TARGET_NAME"
"$BOP" click-js-text "$SESSION_ID" "$TARGET_NAME" || true
"$BOP" wait "$SESSION_ID" 3000 >/dev/null || true
TARGET_READ_JS="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$TARGET_READ_JS"

echo
echo "[10/14] Special fallback for Disks/VJBOD tab..."
if [ "$TARGET_NAME" = "Disks/VJBOD" ]; then
  "$BOP" click-js-text "$SESSION_ID" "Overview" >/dev/null 2>&1 || true
  "$BOP" wait "$SESSION_ID" 1200 >/dev/null || true
  "$BOP" click-js-text "$SESSION_ID" "Disks/VJBOD" >/dev/null 2>&1 || true
  "$BOP" wait "$SESSION_ID" 2500 >/dev/null || true
fi
TARGET_READ_SPECIAL="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$TARGET_READ_SPECIAL"

echo
echo "[11/14] Clearing modal buttons after target..."
"$BOP" click-text "$SESSION_ID" "OK" >/dev/null 2>&1 || true
"$BOP" wait "$SESSION_ID" 1200 >/dev/null || true
"$BOP" click-text "$SESSION_ID" "Cancel" >/dev/null 2>&1 || true
"$BOP" wait "$SESSION_ID" 1200 >/dev/null || true
POST_TARGET_CLEAR="$($BOP read "$SESSION_ID" || true)"
printf '%s\n' "$POST_TARGET_CLEAR"

echo
echo "[12/14] Capturing DOM snapshot..."
DOM_SNAPSHOT="$($BOP dom-snapshot "$SESSION_ID" || true)"
printf '%s\n' "$DOM_SNAPSHOT"

echo
echo "[13/14] Capturing screenshot and clickables..."
SHOT_NAME="browser-operator-open-$(safe_name "$APP_NAME")__$(safe_name "$TARGET_NAME").png"
"$BOP" screenshot "$SESSION_ID" "$SHOT_NAME" || true
FINAL_CLICKS="$($BOP list-clickable "$SESSION_ID" || true)"
printf '%s\n' "$FINAL_CLICKS"

APP_PRESENT="no"
TARGET_PRESENT="no"

if need_text "$APP_NAME" "$APP_READ_NORMAL" || need_text "$APP_NAME" "$APP_READ_JS" || need_text "$APP_NAME" "$APP_READ_REOPEN" || need_text "$APP_NAME" "$DOM_SNAPSHOT"; then
  APP_PRESENT="yes"
fi

if need_text "$TARGET_NAME" "$TARGET_READ_NORMAL" || \
   need_text "$TARGET_NAME" "$TARGET_READ_JS" || \
   need_text "$TARGET_NAME" "$TARGET_READ_SPECIAL" || \
   need_text "$TARGET_NAME" "$POST_TARGET_CLEAR" || \
   need_text "$TARGET_NAME" "$DOM_SNAPSHOT"; then
  TARGET_PRESENT="yes"
fi

echo
echo "[14/14] Summary..."
echo "===== SUMMARY ====="
echo "App target: $APP_NAME"
echo "Follow-up target: $TARGET_NAME"
echo "Session: $SESSION_ID"
echo "Screenshot: artifacts/$SHOT_NAME"
echo "App target present after navigation: $APP_PRESENT"
echo "Follow-up target present after navigation: $TARGET_PRESENT"
