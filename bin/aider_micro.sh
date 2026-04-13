#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bin/aider_micro.sh "anchored message" path/to/file1 [path/to/file2]
  - Requires a clean working tree.
  - Limits micro tasks to at most two files.
  - Message must explicitly anchor each file using "<basename>::<token>" syntax.
  - Runs aider via bin/aider_local.sh and then make quick.
  - Fails if files outside the allowed list change or no file changes.
USAGE
}

fail() {
  local msg="$1"
  local tag="${2:-general}"
  local code="${3:-1}"
  echo "ERROR[$tag]: $msg" >&2
  exit "$code"
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
  fail "micro lane supports at most two files" "too_many_files"
fi

TARGET_FILES=("$@")

require_action_word() {
  local msg_lower=$1
  local verbs=("add" "update" "replace" "fix" "ensure" "enforce" "guard" "patch" "inject" "limit" "rename" "pin" "bound" "restrict")
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
  local min_chars=40
  if [ "${#msg}" -lt "$min_chars" ]; then
    fail "message too short for micro lane (min ${min_chars} chars)" "weak_prompt"
  fi
  if ! require_action_word "$msg_lower"; then
    fail "message must include a concrete action verb (add/update/replace/...)" "weak_prompt"
  fi
  local banned_phrases=(
    "reword" "rephrase" "clarify wording" "rewrite paragraph" "touch docs" "touch documentation"
    "update readme" "polish wording" "cleanup wording" "describe" "explain" "document" "summarize"
  )
  for phrase in "${banned_phrases[@]}"; do
    if printf '%s' "$msg_lower" | grep -q "$phrase"; then
      fail "micro lane rejects doc-style prompt ('$phrase'); use docs workflow" "doc_prompt"
    fi
  done

  local detected_kind="code-adjacent"
  if printf '%s' "$msg_lower" | grep -q "comment"; then
    detected_kind="comment-only"
  elif printf '%s' "$msg_lower" | grep -q "string"; then
    detected_kind="string-edit"
  elif printf '%s' "$msg_lower" | grep -q "guard"; then
    detected_kind="guard"
  fi
  info "task kind detected: $detected_kind"

  for f in "${TARGET_FILES[@]}"; do
    local base
    base=$(basename "$f" | tr '[:upper:]' '[:lower:]')
    if ! printf '%s' "$msg_lower" | grep -q "$base"; then
      fail "message must explicitly mention target file '$base'" "missing_file_ref"
    fi
    if ! printf '%s' "$msg_lower" | grep -q "$base::"; then
      fail "message must anchor '$base' using '<file>::<token>' syntax" "missing_anchor"
    fi
  done
}

ensure_clean_tree() {
  if [ -n "$(git status --porcelain)" ]; then
    fail "working tree must be clean before running aider_micro" "dirty_tree"
  fi
}

ensure_allowed_files() {
  local allowed_prefixes=("shell/" "src/" "tests/" "bin/" "config/" "Makefile" "browser_operator" "operator_task.sh" "start_" "run_" "update_")
  for f in "${TARGET_FILES[@]}"; do
    if [ ! -e "$f" ]; then
      fail "file '$f' does not exist" "missing_file"
    fi
    if [ -d "$f" ]; then
      fail "'$f' is a directory" "bad_target"
    fi
    case "$f" in
      /*)
        fail "use repository-relative paths (got '$f')" "bad_target"
        ;;
      README*|docs/*|AGENTS.md|*.md)
        fail "doc/markdown targets are blocked in the micro lane ('$f')" "doc_target"
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
    case "$f" in
      *.sh|*.py)
        ok=true
        ;;
    esac
    if [ "$ok" = false ]; then
      fail "micro lane only supports code-adjacent files (got '$f')" "bad_target"
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
  status=$?
  if [ "$status" -eq 0 ]; then
    status=99
  fi
  fail "aider exited non-zero (status $status). Inspect artifacts/aider_runs for details." "aider_exit" "$status"
fi

info "running quick validation"
if ! PYTHONPYCACHEPREFIX=/tmp/aider_pycache make quick >/dev/null; then
  fail "make quick failed; inspect quick logs" "validation"
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
    fail "micro run touched disallowed file '$nf'" "scope_violation"
  fi
done

changed_any=false
for f in "${TARGET_FILES[@]}"; do
  if ! git diff --quiet -- "$f"; then
    changed_any=true
  fi
done

if [ "$changed_any" = false ]; then
  fail "none of the target files changed" "no_change"
fi

info "success"
run_count_file="artifacts/micro_runs/count.txt"
mkdir -p "$(dirname "$run_count_file")"
if [ ! -f "$run_count_file" ]; then
  echo 0 >"$run_count_file"
fi
count=$(cat "$run_count_file" || echo 0)
count=$((count + 1))
echo "$count" >"$run_count_file"
info "micro run #$count succeeded"

summary_path="artifacts/micro_runs/last_summary.txt"
cat >"$summary_path" <<SUMMARY
status: success
run_number: $count
files: ${TARGET_FILES[*]}
message: $MESSAGE
timestamp: $(date -Is)
SUMMARY
info "wrote summary to $summary_path"
