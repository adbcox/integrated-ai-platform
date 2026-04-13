#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bin/aider_micro.sh "message" path/to/file1 [path/to/file2]
  - Requires a clean working tree.
  - Limits micro tasks to at most two files.
  - Runs aider via bin/aider_local.sh and then make quick.
  - Fails if files outside the allowed list change or no file changes.
USAGE
}

if [ $# -lt 2 ]; then
  usage >&2
  exit 1
fi

MESSAGE=$1
shift

if [ $# -gt 2 ]; then
  echo "ERROR: micro lane supports at most two files" >&2
  exit 1
fi

TARGET_FILES=("$@")

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: working tree must be clean before running aider_micro" >&2
  exit 1
fi

for f in "${TARGET_FILES[@]}"; do
  if [ ! -e "$f" ]; then
    echo "ERROR: file '$f' does not exist" >&2
    exit 1
  fi
  if [ -d "$f" ]; then
    echo "ERROR: '$f' is a directory" >&2
    exit 1
  fi
  case "$f" in
    /*)
      echo "ERROR: use repository-relative paths (got '$f')" >&2
      exit 1
      ;;
  esac
done

before=$(mktemp)
after=$(mktemp)
trap 'rm -f "$before" "$after"' EXIT

git diff --name-only | sort >"$before"

echo "[micro] running aider on ${TARGET_FILES[*]}"
if ! bash bin/aider_local.sh --message "$MESSAGE" "${TARGET_FILES[@]}"; then
  echo "ERROR: aider exited non-zero" >&2
  exit 1
fi

PYTHONPYCACHEPREFIX=/tmp/aider_pycache make quick >/dev/null

git diff --name-only | sort >"$after"
new_files=$(comm -13 "$before" "$after")

is_allowed() {
  local candidate=$1
  for f in "${TARGET_FILES[@]}"; do
    if [ "$f" = "$candidate" ]; then
      return 0
    fi
  done
  return 1
}

for nf in $new_files; do
  case "$nf" in
    .aider*|.gitignore)
      continue
      ;;
  esac
  if ! is_allowed "$nf"; then
    echo "ERROR: micro run touched disallowed file '$nf'" >&2
    exit 1
  fi
done

changed_any=false
for f in "${TARGET_FILES[@]}"; do
  if ! git diff --quiet -- "$f"; then
    changed_any=true
  fi
done

if [ "$changed_any" = false ]; then
  echo "ERROR: none of the target files changed" >&2
  exit 1
fi

echo "[micro] success"
