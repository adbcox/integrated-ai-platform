#!/bin/sh
set -eu

usage() {
  echo "Usage: $0 <file> [baseline_file]" >&2
  exit 2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  usage
fi

target="$1"
baseline="${2:-}"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "ERROR: must run inside git repo" >&2
  exit 1
fi

if [ ! -f "$target" ]; then
  echo "ERROR: file not found: $target" >&2
  exit 1
fi

if [ -n "$baseline" ] && [ ! -f "$baseline" ]; then
  echo "ERROR: baseline not found: $baseline" >&2
  exit 1
fi

tmp_diff="$(mktemp "${TMPDIR:-/tmp}/comment-only.diff.XXXXXX")"
cleanup() {
  rm -f "$tmp_diff"
}
trap cleanup EXIT INT TERM

if [ -n "$baseline" ]; then
  if ! diff -u "$baseline" "$target" >"$tmp_diff"; then
    true
  fi
else
  if ! git diff -- "$target" >"$tmp_diff"; then
    echo "[comment-only] Unable to compute diff for $target" >&2
    exit 1
  fi
fi

if [ ! -s "$tmp_diff" ]; then
  echo "[comment-only] No changes detected for $target"
  exit 0
fi

violations=0
while IFS= read -r line; do
  case "$line" in
    ---*|+++*|@@*|"")
      continue
      ;;
  esac

  first_char=$(printf '%s' "$line" | cut -c1-1)
  if [ "$first_char" != "+" ] && [ "$first_char" != "-" ]; then
    continue
  fi

  content=$(printf '%s' "$line" | cut -c2-)
  trimmed=$(printf '%s' "$content" | sed 's/^[[:space:]]*//')

  if [ -z "$trimmed" ]; then
    continue
  fi

  case "$trimmed" in
    \#*)
      continue
      ;;
  esac

  violations=1
  if [ "$first_char" = "+" ]; then
    printf '[comment-only] Added non-comment line: %s\n' "$line" >&2
  else
    printf '[comment-only] Removed non-comment line: %s\n' "$line" >&2
  fi
done <"$tmp_diff"

if [ "$violations" -ne 0 ]; then
  echo "ERROR: $target has non-comment changes" >&2
  exit 1
fi

echo "[comment-only] OK: $target changes limited to comments/blank lines"
