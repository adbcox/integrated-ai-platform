#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BOP="${BOP:-$BASE/bop.sh}"
LOGIN_FLOW="${LOGIN_FLOW:-$BASE/browser_operator_login_flow.sh}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$BASE/artifacts}"
APP_NAME="${APP_NAME:-Container Station}"
TARGET_NAME="${TARGET_NAME:-deluge}"
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

mkdir -p "$ARTIFACT_DIR"

POST_APP_JS_READ=""
POST_CLEAR_READ=""
POST_TARGET_READ=""
POST_TARGET_JS_READ=""
POST_TARGET_CLICKABLES=""
TARGET_SELECTION_RAN=0
TARGET_VERIFIED=0
BLOCKER_REMAINS=0

safe_name() {
  printf '%s' "$1" | tr ' /' '__' | tr -cd '[:alnum:]_.-'
}

need_text() {
  needle="$1"
  haystack="$2"
  printf '%s' "$haystack" | grep -F "$needle" >/dev/null 2>&1
}

modal_blocked_found() {
  haystack="$1"
  need_text "Firmware Update" "$haystack" || \
    need_text "New firmware updates are available" "$haystack" || \
    need_text "firmware updates are available" "$haystack" || \
    (need_text "Update" "$haystack" && need_text "Cancel" "$haystack")
}

container_context_found() {
  haystack="$1"
  printf '%s' "$haystack" | grep -Ei 'Container Station|containers?|Images|Applications' >/dev/null 2>&1
}

container_interaction_verified() {
  haystack="$1"
  need_text "$TARGET_NAME" "$haystack" || return 1
  container_context_found "$haystack" || return 1
  printf '%s' "$haystack" | grep -Ei 'Start|Stop|Restart|Console|Terminal|Logs|Details|CPU|Memory|Image|Ports?' >/dev/null 2>&1
}

candidate_blocked_context() {
  line="$1"
  line_lc="$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')"
  case "$line_lc" in
    *notice\ board*|*file\ station*|*desktop*|*sidebar*|*breadcrumb*|*tree*|*launcher*|*taskbar*|*main\ menu*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

find_target_index() {
  clickables="$1"
  target_lc="$(printf '%s' "$TARGET_NAME" | tr '[:upper:]' '[:lower:]')"
  printf '%s\n' "$clickables" | while IFS= read -r line; do
    line_lc="$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')"
    case "$line_lc" in
      *\"label\"*"$target_lc"*)
        if candidate_blocked_context "$line"; then
          continue
        fi
        idx="$(printf '%s\n' "$line" | sed -n 's/.*"index":\([0-9][0-9]*\).*/\1/p' | head -n 1)"
        if [ -n "$idx" ]; then
          printf '%s\n' "$idx"
          break
        fi
        ;;
    esac
  done
}

echo
echo "=================================================="
echo "TASK: open-target"
echo "=================================================="

echo "[1/12] Running shared login flow..."
LOGIN_OUT="$($LOGIN_FLOW 2>&1 || true)"
echo "$LOGIN_OUT"

SESSION_ID="$(extract_session_id "$LOGIN_OUT" || true)"
if [ -z "$SESSION_ID" ]; then
  echo "Failed to obtain session id." >&2
  exit 1
fi

echo "[2/12] Reading initial desktop state..."
INITIAL_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$INITIAL_READ"

echo "[3/12] Opening app: $APP_NAME"
APP_CLICK="$($BOP click-text "$SESSION_ID" "$APP_NAME" 2>&1 || true)"
echo "$APP_CLICK"
POST_APP_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$POST_APP_READ"

echo "[4/12] Fallback JS open app: $APP_NAME"
APP_CLICK_JS="$($BOP click-js-text "$SESSION_ID" "$APP_NAME" 2>&1 || true)"
echo "$APP_CLICK_JS" | head -n 10
"$BOP" wait "$SESSION_ID" 1200 >/dev/null 2>&1 || true
POST_APP_JS_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$POST_APP_JS_READ" | head -n 10

echo "[5/12] Checking for blocking modal/mask..."
if modal_blocked_found "$POST_APP_READ
$POST_APP_JS_READ"; then
  echo "Blocking modal detected, attempting dismissal..."
  for attempt in 1 2 3; do
    echo "Attempt $attempt: Clicking Cancel (firmware dismiss)..."
    CANCEL_OUT="$($BOP click-text "$SESSION_ID" "Cancel" 2>&1 || true)"
    echo "$CANCEL_OUT" | head -n 3
    CANCEL_JS_OUT="$($BOP click-js-text "$SESSION_ID" "Cancel" 2>&1 || true)"
    echo "$CANCEL_JS_OUT" | head -n 3
    LATER_OUT="$($BOP click-text "$SESSION_ID" "Later" 2>&1 || true)"
    echo "$LATER_OUT" | head -n 3
    "$BOP" wait "$SESSION_ID" 1000 >/dev/null 2>&1 || true
    echo "Attempt $attempt: Clicking OK..."
    OK_OUT="$($BOP click-text "$SESSION_ID" "OK" 2>&1 || true)"
    echo "$OK_OUT" | head -n 3
    "$BOP" wait "$SESSION_ID" 1000 >/dev/null 2>&1 || true
    POST_CLEAR_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
    if ! modal_blocked_found "$POST_CLEAR_READ"; then
      echo "Modal cleared on attempt $attempt."
      break
    else
      echo "Modal still present after attempt $attempt."
    fi
  done
  if modal_blocked_found "$POST_CLEAR_READ"; then
    BLOCKER_REMAINS=1
  fi
else
  POST_CLEAR_READ="$POST_APP_JS_READ"
fi

echo "[6/12] Selecting target: $TARGET_NAME"
CLICKABLES_OUT="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
echo "$CLICKABLES_OUT" | head -n 20
TARGET_INDEX="$(find_target_index "$CLICKABLES_OUT" | head -n 1)"
if [ -n "$TARGET_INDEX" ]; then
  echo "Found context-specific target candidate at index $TARGET_INDEX, clicking..."
  TARGET_CLICK="$($BOP click-index "$SESSION_ID" "$TARGET_INDEX" 2>&1 || true)"
  echo "$TARGET_CLICK" | head -n 5
  TARGET_SELECTION_RAN=1
  "$BOP" wait "$SESSION_ID" 2500 >/dev/null 2>&1 || true
  POST_TARGET_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
  echo "$POST_TARGET_READ" | head -n 10
else
  echo "No context-specific index candidate found."
  if [ "$BLOCKER_REMAINS" -eq 0 ] && container_context_found "$POST_CLEAR_READ
$CLICKABLES_OUT"; then
    echo "Using container-context fallback target click."
    TARGET_CLICK="$($BOP click-js-text "$SESSION_ID" "$TARGET_NAME" 2>&1 || true)"
    echo "$TARGET_CLICK" | head -n 5
    TARGET_SELECTION_RAN=1
    "$BOP" wait "$SESSION_ID" 2500 >/dev/null 2>&1 || true
    POST_TARGET_READ="$($BOP read "$SESSION_ID" 2>&1 || true)"
    echo "$POST_TARGET_READ" | head -n 10
  else
    echo "Fallback click skipped because container context is not strong enough."
  fi
fi

echo "[7/12] Verifying target interaction..."
if [ "$TARGET_SELECTION_RAN" -eq 1 ]; then
  POST_TARGET_JS_READ="$($BOP dom-snapshot "$SESSION_ID" 2>&1 || true)"
  POST_TARGET_CLICKABLES="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
  if container_interaction_verified "$POST_TARGET_READ
$POST_TARGET_JS_READ
$POST_TARGET_CLICKABLES"; then
    TARGET_VERIFIED=1
    echo "Post-click verification succeeded."
  else
    echo "Post-click verification did not confirm container-level interaction."
  fi
else
  echo "Target-selection branch did not run."
fi

echo "[8/12] Capture DOM snapshot..."
DOM_SNAPSHOT="$($BOP dom-snapshot "$SESSION_ID" 2>&1 || true)"
echo "$DOM_SNAPSHOT"

echo "[9/12] Capture clickables..."
CLICKABLES="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
echo "$CLICKABLES"

echo "[10/12] Capture screenshot..."
SHOT_NAME="browser-operator-open-$(safe_name "$APP_NAME")__$(safe_name "$TARGET_NAME").png"
SCREENSHOT_OUT="$($BOP screenshot "$SESSION_ID" "$ARTIFACT_DIR/$SHOT_NAME" 2>&1 || true)"
echo "$SCREENSHOT_OUT"

echo "[11/12] Aggregate evidence..."
ALL_EVIDENCE="${INITIAL_READ}
${POST_APP_READ}
${POST_APP_JS_READ}
${POST_CLEAR_READ}
${POST_TARGET_READ}
${POST_TARGET_JS_READ}
${POST_TARGET_CLICKABLES}
${DOM_SNAPSHOT}
${CLICKABLES}"

RESULT_STATE="fail"

if [ "$BLOCKER_REMAINS" -eq 1 ] && modal_blocked_found "$POST_CLEAR_READ
$POST_TARGET_READ
$POST_TARGET_JS_READ"; then
  RESULT_STATE="modal-blocked"
elif [ "$TARGET_SELECTION_RAN" -eq 1 ] && [ "$TARGET_VERIFIED" -eq 1 ]; then
  RESULT_STATE="deep-loaded"
fi

echo "[12/12] Final result..."
case "$RESULT_STATE" in
  deep-loaded)
    echo "PASS"
    "$BOP" close "$SESSION_ID" >/dev/null 2>&1 || true
    exit 0
    ;;
  modal-blocked)
    echo "BLOCKED"
    "$BOP" close "$SESSION_ID" >/dev/null 2>&1 || true
    exit 2
    ;;
  *)
    echo "FAIL"
    "$BOP" close "$SESSION_ID" >/dev/null 2>&1 || true
    exit 1
    ;;
esac
