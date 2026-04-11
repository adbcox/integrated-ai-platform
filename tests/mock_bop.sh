#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
COMMON_SH="${COMMON_SH:-$SCRIPT_DIR/../shell/common.sh}"
SCENARIO_FILE="${SCENARIO_FILE:-}"
MOCK_BOP_STATE_DIR="${MOCK_BOP_STATE_DIR:-}"

if [ -n "$SCENARIO_FILE" ] && [ -r "$SCENARIO_FILE" ]; then
  # shellcheck disable=SC1090
  . "$SCENARIO_FILE"
fi

if [ -z "$MOCK_BOP_STATE_DIR" ]; then
  echo "ERROR: MOCK_BOP_STATE_DIR is required for mock_bop.sh" >&2
  exit 1
fi
mkdir -p "$MOCK_BOP_STATE_DIR"

if [ -r "$COMMON_SH" ]; then
  # shellcheck disable=SC1090
  . "$COMMON_SH"
fi

MOCK_SESSION_ID="${MOCK_SESSION_ID:-mock-session-123}"
MOCK_START_JSON="${MOCK_START_JSON:-{\"session_id\":\"$MOCK_SESSION_ID\",\"status\":\"started\"}}"
MOCK_OPEN_JSON="${MOCK_OPEN_JSON:-{\"session_id\":\"$MOCK_SESSION_ID\",\"status\":\"opened\"}}"
MOCK_CLOSE_JSON="${MOCK_CLOSE_JSON:-{\"session_id\":\"$MOCK_SESSION_ID\",\"status\":\"closed\"}}"
MOCK_READ_DEFAULT="${MOCK_READ_DEFAULT:-}"
MOCK_DOM_SNAPSHOT_DEFAULT="${MOCK_DOM_SNAPSHOT_DEFAULT:-$MOCK_READ_DEFAULT}"
MOCK_LIST_CLICKABLE_DEFAULT="${MOCK_LIST_CLICKABLE_DEFAULT:-{\"index\":1,\"tag\":\"button\",\"label\":\"noop\"}}"

next_count() {
  key="$1"
  count_file="$MOCK_BOP_STATE_DIR/$key.count"
  current="0"
  if [ -f "$count_file" ]; then
    current="$(cat "$count_file")"
  fi
  next=$((current + 1))
  printf '%s' "$next" >"$count_file"
  printf '%s\n' "$next"
}

value_for() {
  prefix="$1"
  idx="$2"
  default_value="$3"
  eval "val=\${${prefix}_${idx}:-}"
  if [ -n "${val:-}" ]; then
    printf '%s\n' "$val"
    return 0
  fi
  eval "val=\${${prefix}_DEFAULT:-}"
  if [ -n "${val:-}" ]; then
    printf '%s\n' "$val"
    return 0
  fi
  printf '%s\n' "$default_value"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  start)
    printf '%s\n' "$MOCK_START_JSON"
    ;;
  open)
    printf '%s\n' "$MOCK_OPEN_JSON"
    ;;
  close)
    printf '%s\n' "$MOCK_CLOSE_JSON"
    ;;
  read)
    idx="$(next_count read)"
    value_for MOCK_READ "$idx" "{}"
    ;;
  dom-snapshot)
    idx="$(next_count dom_snapshot)"
    value_for MOCK_DOM_SNAPSHOT "$idx" "{}"
    ;;
  list|list-clickable)
    idx="$(next_count list_clickable)"
    value_for MOCK_LIST_CLICKABLE "$idx" '{"index":1,"tag":"button","label":"noop"}'
    ;;
  click-text|click-js-text|click-selector|click-index|type|fill-input-index|press|wait)
    printf '{"session_id":"%s","action":"%s","status":"ok"}\n' "$MOCK_SESSION_ID" "$cmd"
    ;;
  screenshot)
    name="${2:-shot.png}"
    printf '{"session_id":"%s","screenshot_path":"%s"}\n' "$MOCK_SESSION_ID" "$name"
    ;;
  *)
    echo "ERROR: unsupported mock bop command: $cmd" >&2
    exit 1
    ;;
esac
