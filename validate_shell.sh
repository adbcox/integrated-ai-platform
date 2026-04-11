#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
COMMON_SH="$BASE_DIR/shell/common.sh"

if [ ! -r "$COMMON_SH" ]; then
  echo "ERROR: missing shared helper: $COMMON_SH" >&2
  exit 1
fi

echo "[1/3] Syntax-checking active shell scripts..."
find "$BASE_DIR" -maxdepth 1 -type f -name '*.sh' \
  ! -name '*.bak.*' \
  ! -name '*.bad_*' \
  ! -name 'qnap_*' \
  | sort \
  | while IFS= read -r file; do
      sh -n "$file"
      echo "OK: $(basename "$file")"
    done

echo
echo "[2/3] Syntax-checking shared shell helpers..."
find "$BASE_DIR/shell" -type f -name '*.sh' | sort | while IFS= read -r file; do
  sh -n "$file"
  echo "OK: shell/$(basename "$file")"
done

echo
echo "[3/3] Running helper smoke tests..."
json_out="$(sh -c '. "$1"; extract_session_id "{\"session_id\":\"abc-123\"}"' sh "$COMMON_SH")"
if [ "$json_out" != "abc-123" ]; then
  echo "ERROR: extract_session_id JSON parse failed: $json_out" >&2
  exit 1
fi

line_out="$(sh -c '. "$1"; extract_session_id "Using session: abc-123"' sh "$COMMON_SH")"
if [ "$line_out" != "abc-123" ]; then
  echo "ERROR: extract_session_id line parse failed: $line_out" >&2
  exit 1
fi

require_out="$(sh -c '. "$1"; require_exec sh && echo ok' sh "$COMMON_SH")"
if [ "$require_out" != "ok" ]; then
  echo "ERROR: require_exec smoke test failed: $require_out" >&2
  exit 1
fi

echo "PASS: shell validation complete."
