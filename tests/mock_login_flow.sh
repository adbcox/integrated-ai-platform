#!/bin/sh
set -eu

SCENARIO_FILE="${SCENARIO_FILE:-}"
if [ -n "$SCENARIO_FILE" ] && [ -r "$SCENARIO_FILE" ]; then
  # shellcheck disable=SC1090
  . "$SCENARIO_FILE"
fi

MOCK_SESSION_ID="${MOCK_SESSION_ID:-mock-session-123}"
MOCK_LOGIN_FLOW_MODE="${MOCK_LOGIN_FLOW_MODE:-normal}"

echo "[mock-login] scenario mode: $MOCK_LOGIN_FLOW_MODE"

case "$MOCK_LOGIN_FLOW_MODE" in
  normal)
    echo "Using session: $MOCK_SESSION_ID"
    echo "$MOCK_SESSION_ID"
    ;;
  raw-only)
    echo "$MOCK_SESSION_ID"
    ;;
  missing-session)
    echo "login complete without session marker"
    ;;
  *)
    echo "ERROR: unknown MOCK_LOGIN_FLOW_MODE: $MOCK_LOGIN_FLOW_MODE" >&2
    exit 1
    ;;
esac
