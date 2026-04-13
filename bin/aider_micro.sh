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

fail() {
  echo "ERROR: $1" >&2
  exit "${2:-1}"
}

info() {
  echo "[micro] $1"
}

if [ $# -lt 2 ]; then
  usage >&2
  exit 1
fi

MESSAGE=$1
shift

if [ $# -gt 2 ]; then
  fail "micro lane supports at most two files"
fi

TARGET_FILES=("$@")

require_action_word() {
  local msg_lower=$1
  local verbs=("add" "update" "replace" "fix" "ensure" "enforce" "guard" "comment" "docstring" "patch" "inject" "limit" "rename")
  for verb in "${verbs[@]}"; do
    if printf '%s' "$msg_lower" | grep -q "\\b$verb\\b"; then
      return 0
    fi
  done
  return 1
}

ensure_message_quality() {
  local msg="$1"
  local msg_lower
  msg_lower=$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')
  local min_chars=30
  if [ "${#msg}" -lt "$min_chars" ]; then
    fail "message too short for micro lane (min ${min_chars} chars)"
  fi
  if ! require_action_word "$msg_lower"; then
    fail "message must include a concrete action verb (add/update/replace/...)"
  fi
  local banned_phrases=("reword" "rephrase" "clarify wording" "rewrite paragraph" "touch docs" "touch documentation" "update README" "polish wording" "cleanup wording")
  for phrase in "${banned_phrases[@]}"; do
    if printf '%s' "$msg_lower" | grep -q "$phrase"; then
      fail "micro lane rejects vague doc prompt ('$phrase'); use a docs-specific workflow"
    fi
  done
  for f in "${TARGET_FILES[@]}"; do
    local base
    base=$(basename "$f" | tr '[:upper:]' '[:lower:]')
    if ! printf '%s' "$msg_lower" | grep -q "$base"; then
      fail "message must explicitly mention target file '$base'"
    fi
  done
}

ensure_clean_tree() {
  if [ -n "$(git status --porcelain)" ]; then
    fail "working tree must be clean before running aider_micro"
  fi
}

ensure_allowed_files() {
  local allowed_prefixes=("shell/" "src/" "tests/" "bin/" "config/" "Makefile")
  for f in "${TARGET_FILES[@]}"; do
    if [ ! -e "$f" ]; then
      fail "file '$f' does not exist"
    fi
    if [ -d "$f" ]; then
      fail "'$f' is a directory"
    fi
    case "$f" in
      /*)
        fail "use repository-relative paths (got '$f')"
        ;;
      README*|docs/*|AGENTS.md|*.md)
        fail "doc/markdown targets are blocked in the micro lane ('$f')"
        ;;
    esac
    local ok=false
    for prefix in "${allowed_prefixes[@]}"; do
      case "$f" in
        "$prefix"*)
          ok=true
          break
          ;;
        "$prefix")
          ok=true
          break
          ;;
      esac
    done
    if [ "$ok" = false ]; then
      fail "micro lane only supports code-adjacent files (got '$f')"
    fi
  done
}

ensure_clean_tree
ensure_message_quality "$MESSAGE"
ensure_allowed_files

before=$(mktemp)
after=$(mktemp)
trap 'rm -f "$before" "$after"' EXIT

git diff --name-only | sort >"$before"

info "running aider on ${TARGET_FILES[*]}"
if ! bash bin/aider_local.sh --message "$MESSAGE" "${TARGET_FILES[@]}"; then
  fail "aider exited non-zero (see artifacts under artifacts/aider_runs/)"
fi

info "running quick validation"
if ! PYTHONPYCACHEPREFIX=/tmp/aider_pycache make quick >/dev/null; then
  fail "make quick failed; inspect quick logs"
fi

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
    fail "micro run touched disallowed file '$nf'"
  fi
done

changed_any=false
for f in "${TARGET_FILES[@]}"; do
  if ! git diff --quiet -- "$f"; then
    changed_any=true
  fi
done

if [ "$changed_any" = false ]; then
  fail "none of the target files changed"
fi

info "success"
