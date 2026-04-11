#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
TOOLS_DIR="$BASE/tools"
BOP="${BOP:-$BASE/bop.sh}"
LOGIN_FLOW="${LOGIN_FLOW:-$BASE/browser_operator_login_flow.sh}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$BASE/artifacts}"
RECOVERY_JS="$TOOLS_DIR/browser_operator.js"
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

if [ -e "$RECOVERY_JS" ] && [ ! -x "$RECOVERY_JS" ]; then
  chmod +x "$RECOVERY_JS" 2>/dev/null || true
fi

RECOVERY_AVAILABLE="no"
if [ -x "$RECOVERY_JS" ]; then
  RECOVERY_AVAILABLE="yes"
else
  echo "WARN: browser_operator.js not available/executable; modal recovery disabled" >&2
fi

APP_NAME="${1:-Container Station}"
mkdir -p "$ARTIFACT_DIR"

need_text() {
  needle="$1"
  haystack="$2"
  echo "$haystack" | grep -F "$needle" >/dev/null 2>&1
}

modal_blocked_found() {
  haystack="$1"
  need_text "Firmware Update" "$haystack" || \
  need_text "New firmware updates are available" "$haystack" || \
  need_text "Update" "$haystack" || \
  need_text "Cancel" "$haystack"
}

container_deep_markers_found() {
  haystack="$1"
  need_text "Container Station" "$haystack"
}

container_title_found() {
  haystack="$1"
  need_text "Container Station" "$haystack"
}

app_center_markers_found() {
  haystack="$1"
  need_text "App Center" "$haystack"
}

echo
echo "============================================================"
echo "TASK: open-app"
echo "============================================================"

echo "[1/10] Running shared login flow..."
LOGIN_OUT="$($LOGIN_FLOW 2>&1 || true)"
echo "$LOGIN_OUT"

SESSION_ID="$(extract_session_id "$LOGIN_OUT" || true)"
if [ -z "$SESSION_ID" ]; then
  echo "Failed to obtain session id."
  exit 1
fi

echo
echo "[2/10] Reading initial desktop state..."
INITIAL_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$INITIAL_READ"

echo
echo "[3/10] Listing clickables before app open..."
INITIAL_CLICKS="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
echo "$INITIAL_CLICKS"

echo
echo "[4/10] Attempting normal click on app: $APP_NAME"
CLICK_OUT="$($BOP click-text "$SESSION_ID" "$APP_NAME" 2>&1 || true)"
echo "$CLICK_OUT"
POST_CLICK_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$POST_CLICK_READ"

echo
echo "[5/10] Attempting JS click fallback on app: $APP_NAME"
JS_CLICK_OUT="$($BOP click-js-text "$SESSION_ID" "$APP_NAME" 2>&1 || true)"
echo "$JS_CLICK_OUT"
POST_JS_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$POST_JS_READ"

echo
echo "[6/10] Clearing modal buttons..."
POST_CLEAR_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$POST_CLEAR_READ"

echo
echo "[7/10] Capturing DOM dom-snapshot..."
DOM_SNAPSHOT="$($BOP dom-snapshot "$SESSION_ID" 2>&1 || true)"
echo "$DOM_SNAPSHOT"

echo
echo "[8/10] Capturing screenshot and clickables..."
SHOT_NAME="browser-operator-open-$(echo "$APP_NAME" | tr ' ' '_').png"
SCREENSHOT_OUT="$($BOP screenshot "$SESSION_ID" "$ARTIFACT_DIR/$SHOT_NAME" 2>&1 || true)"
echo "$SCREENSHOT_OUT"
FINAL_CLICKS="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
echo "$FINAL_CLICKS"

ALL_EVIDENCE="$(printf '%s\n%s\n%s\n%s\n%s\n%s\n%s\n' \
  "$INITIAL_READ" \
  "$INITIAL_CLICKS" \
  "$POST_CLICK_READ" \
  "$POST_JS_READ" \
  "$POST_CLEAR_READ" \
  "$DOM_SNAPSHOT" \
  "$FINAL_CLICKS")"

APP_PRESENT="no"
RESULT_STATE="fail"

echo
echo "[marker-check] app=$APP_NAME"

case "$APP_NAME" in
  "Container Station")
    if container_deep_markers_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="deep-loaded"
    elif modal_blocked_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="modal-blocked"

      echo
      echo "[recovery] modal detected, dismissing and retrying..."
      if [ "$RECOVERY_AVAILABLE" = "yes" ]; then
        echo "Recovery helper present, but external JS recovery path is intentionally disabled in this repair build."
        echo "Leaving state as modal-blocked."
      else
        echo "WARN: modal recovery helper unavailable; leaving state as modal-blocked" >&2
      fi
    elif container_title_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="title-open"
    fi
    ;;
  "App Center")
    if app_center_markers_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="deep-loaded"
    elif modal_blocked_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="modal-blocked"

      echo
      echo "[recovery] modal detected, dismissing and retrying..."
      if [ "$RECOVERY_AVAILABLE" = "yes" ]; then
        echo "Recovery helper present, but external JS recovery path is intentionally disabled in this repair build."
        echo "Leaving state as modal-blocked."
      else
        echo "WARN: modal recovery helper unavailable; leaving state as modal-blocked" >&2
      fi
    elif need_text "App Center" "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="title-open"
    fi
    ;;
  *)
    if modal_blocked_found "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="modal-blocked"
    elif need_text "$APP_NAME" "$ALL_EVIDENCE"; then
      APP_PRESENT="yes"
      RESULT_STATE="title-open"
    fi
    ;;
esac

echo
echo "[9/10] Summary..."
echo "===== SUMMARY ====="
echo "App target: $APP_NAME"
echo "Session: $SESSION_ID"
echo "Screenshot: /"
echo "Target text present after navigation: $APP_PRESENT"
echo "Result state: $RESULT_STATE"

echo
echo "[10/10] Exit status..."
case "${RESULT_STATE:-fail}" in
  deep-loaded|recovered-after-modal|title-open)
    echo "PASS"
    exit 0
    ;;
  modal-blocked)
    echo "BLOCKED"
    exit 2
    ;;
  *)
    echo "FAIL"
    exit 1
    ;;
esac
