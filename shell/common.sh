#!/bin/sh

# Shared POSIX shell helpers for browser operator scripts.

require_exec() {
  target="$1"
  if [ -x "$target" ]; then
    return 0
  fi
  command -v "$target" >/dev/null 2>&1 || {
    echo "Missing required command or executable: $target" >&2
    return 1
  }
}

extract_json_field() {
  key="$1"
  sed -n "s/.*\"$key\":\"\([^\"]*\)\".*/\1/p"
}

extract_session_id() {
  input="$1"
  session_id="$(printf '%s\n' "$input" | extract_json_field session_id | tail -n 1)"
  if [ -n "$session_id" ]; then
    printf '%s\n' "$session_id"
    return 0
  fi

  session_id="$(printf '%s\n' "$input" | sed -n 's/^Using session: \(.*\)$/\1/p' | tail -n 1)"
  if [ -n "$session_id" ]; then
    printf '%s\n' "$session_id"
    return 0
  fi

  session_id="$(printf '%s\n' "$input" | grep -E '^[0-9a-f][0-9a-f-]*$' | tail -n 1 || true)"
  if [ -n "$session_id" ]; then
    printf '%s\n' "$session_id"
    return 0
  fi

  return 1
}
