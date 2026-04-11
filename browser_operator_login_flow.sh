#!/bin/sh
set -eu

BASE="${BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
BOP="${BOP:-$BASE/bop.sh}"
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

LOGIN_URL="${LOGIN_URL:-https://192.168.10.114/cgi-bin/}"
QNAP_USER="${QNAP_USER:-admin}"
QNAP_PASS="${QNAP_PASS:-}"

SESSION_JSON="$($BOP start)"
echo "$SESSION_JSON"

SESSION_ID="$(extract_session_id "$SESSION_JSON" || true)"
if [ -z "$SESSION_ID" ]; then
  echo "Failed to obtain session id." >&2
  exit 1
fi

echo "Using session: $SESSION_ID"
echo

OPEN_OUT="$($BOP open "$SESSION_ID" "$LOGIN_URL" 2>&1 || true)"
echo "$OPEN_OUT"
sleep 2

READ_OUT="$($BOP read "$SESSION_ID" 2>&1 || true)"
echo "$READ_OUT"

# Stage 1: username-first screen
if echo "$READ_OUT" | grep -q 'Auto Detect' && echo "$READ_OUT" | grep -q 'Next'; then
  echo
  echo "[login-flow] Detected username-first login screen."
  echo "[login-flow] Using username: $QNAP_USER"

  TYPE_USER_OUT="$($BOP type "$SESSION_ID" "#username" "$QNAP_USER" 2>&1 || true)"
  echo "$TYPE_USER_OUT"
  sleep 1

  NEXT_OUT="$($BOP click-text "$SESSION_ID" "Next" 2>&1 || true)"
  echo "$NEXT_OUT"
  sleep 2

  READ_OUT="$($BOP read "$SESSION_ID" 2>&1 || true)"
  echo "$READ_OUT"

  CLICKABLES_OUT="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
  echo "$CLICKABLES_OUT"
fi

# Stage 2: password screen
if echo "$READ_OUT" | grep -q 'Login' && echo "$READ_OUT" | grep -q "$QNAP_USER"; then
  echo
  echo "[login-flow] Detected password screen."

  if [ -z "$QNAP_PASS" ]; then
    echo "ERROR: QNAP_PASS is not set." >&2
    echo "$SESSION_ID"
    exit 1
  fi

  TYPE_PASS_OUT="$($BOP type "$SESSION_ID" "input[type=password]" "$QNAP_PASS" 2>&1 || true)"
  echo "$TYPE_PASS_OUT"
  sleep 1

  CLICKABLES_BEFORE_LOGIN="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
  echo "$CLICKABLES_BEFORE_LOGIN"

  LOGIN_INDEX="$(printf '%s' "$CLICKABLES_BEFORE_LOGIN" | tr '{' '\n' | sed -n '/"tag":"button","label":"Login"/s/.*"index":\([0-9][0-9]*\).*/\1/p' | head -n 1)"

  if [ -n "$LOGIN_INDEX" ]; then
    echo "[login-flow] Clicking Login button at index: $LOGIN_INDEX"
    LOGIN_CLICK_OUT="$($BOP click-index "$SESSION_ID" "$LOGIN_INDEX" 2>&1 || true)"
  else
    echo "[login-flow] Login button index not found, falling back to text click."
    LOGIN_CLICK_OUT="$($BOP click-text "$SESSION_ID" "Login" 2>&1 || true)"
  fi
  echo "$LOGIN_CLICK_OUT"
  sleep 4

  READ_AFTER_LOGIN="$($BOP read "$SESSION_ID" 2>&1 || true)"
  echo "$READ_AFTER_LOGIN"

  CLICKABLES_AFTER_LOGIN="$($BOP list-clickable "$SESSION_ID" 2>&1 || true)"
  echo "$CLICKABLES_AFTER_LOGIN"
fi

echo "$SESSION_ID"
