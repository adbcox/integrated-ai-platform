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

RESTORE_ON_FAIL=false

restore_repo_state() {
  if [ "$RESTORE_ON_FAIL" = true ] && [ -n "${HEAD_BEFORE:-}" ]; then
    info "restoring pre-run git state"
    git reset --hard "$HEAD_BEFORE" >/dev/null 2>&1 || true
    git clean -fd >/dev/null 2>&1 || true
  fi
}

fail() {
  local msg="$1"
  local tag="${2:-general}"
  local code="${3:-1}"
  restore_repo_state
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
TASK_KIND="code-adjacent"

is_target_file() {
  local candidate="$1"
  for f in "${TARGET_FILES[@]}"; do
    if [ "$f" = "$candidate" ]; then
      return 0
    fi
  done
  return 1
}

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
  TASK_KIND="$detected_kind"

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

HEAD_BEFORE=$(git rev-parse HEAD)
TEST_MODE=false
if [ -n "${AIDER_MICRO_FAKE_DIFF_FILE:-}" ]; then
  TEST_MODE=true
fi

if [ "$TEST_MODE" = false ]; then
  RESTORE_ON_FAIL=true
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
else
  info "test mode enabled; skipping aider invocation"
fi

if [ "$TEST_MODE" = false ]; then
  HEAD_AFTER=$(git rev-parse HEAD)
else
  HEAD_AFTER="$HEAD_BEFORE"
fi
diff_file=$(mktemp)
trap 'rm -f "$diff_file"' EXIT

declare -a CHANGED_TOTAL
declare -a CHANGED_TARGET

if [ -n "${AIDER_MICRO_FAKE_DIFF_FILE:-}" ]; then
  if [ -z "${AIDER_MICRO_FAKE_FILES:-}" ]; then
    fail "test mode requires AIDER_MICRO_FAKE_FILES" "test_setup"
  fi
  read -r -a CHANGED_TOTAL <<<"${AIDER_MICRO_FAKE_FILES}"
  CHANGED_TARGET=("${CHANGED_TOTAL[@]}")
  cp "$AIDER_MICRO_FAKE_DIFF_FILE" "$diff_file"
elif [ "$HEAD_BEFORE" != "$HEAD_AFTER" ]; then
  mapfile -t CHANGED_TOTAL < <(git diff --name-only "$HEAD_BEFORE" "$HEAD_AFTER")
  mapfile -t CHANGED_TARGET < <(git diff --name-only "$HEAD_BEFORE" "$HEAD_AFTER" -- "${TARGET_FILES[@]}")
  git diff "$HEAD_BEFORE" "$HEAD_AFTER" -- "${TARGET_FILES[@]}" >"$diff_file"
else
  mapfile -t CHANGED_TOTAL < <(git diff --name-only)
  mapfile -t CHANGED_TARGET < <(git diff --name-only -- "${TARGET_FILES[@]}")
  git diff -- "${TARGET_FILES[@]}" >"$diff_file"
fi

changed_any=false
if [ ${#CHANGED_TARGET[@]} -gt 0 ] || [ -s "$diff_file" ]; then
  changed_any=true
fi

if [ "$TEST_MODE" = false ] && [ "$HEAD_BEFORE" != "$HEAD_AFTER" ]; then
  if ! git diff --quiet "$HEAD_BEFORE" "$HEAD_AFTER" -- "${TARGET_FILES[@]}"; then
    changed_any=true
  fi
fi

for nf in "${CHANGED_TOTAL[@]}"; do
  [ -n "$nf" ] || continue
  case "$nf" in
    .aider*|.gitignore)
      continue
      ;;
  esac
  if ! is_target_file "$nf"; then
    fail "micro run touched disallowed file '$nf'" "scope_violation"
  fi
done

if [ "$changed_any" = false ]; then
  fail "none of the target files changed" "no_change"
fi

enforce_comment_scope() {
  local diff_path="$1"
  local current_file=""
  local shell_file=false
  local shell_control_regex='\b(if|then|fi|elif|else|for|while|until|case|esac|select|do|done|return|exit|trap|set|shift|break|continue)\b'
  while IFS= read -r line; do
    case "$line" in
      "+++ "*)
        current_file=${line#+++ b/}
        shell_file=false
        case "$current_file" in
          *.sh|shell/*|bin/*|operator_task.sh|start_*|run_*|update_*|Makefile)
            shell_file=true
            ;;
        esac
        continue
        ;;
      "--- "*|"@@ "*)
        continue
        ;;
      +*|-*)
        local sign=${line:0:1}
        local content=${line:1}
        local trimmed=$(printf '%s' "$content" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        if [ -z "$trimmed" ]; then
          continue
        fi
        if [[ "$trimmed" =~ ^(#|//|/\*|\*/|\*|<!--) ]]; then
          continue
        fi
        if [ "$shell_file" = true ] && [[ "$trimmed" =~ $shell_control_regex ]]; then
          fail "comment-only task changed shell control flow in $current_file (snippet: $trimmed)" "comment_scope"
        fi
        fail "comment-only task modified code in $current_file (line: $trimmed)" "comment_scope"
        ;;
    esac
  done <"$diff_path"
}

if [ "$TASK_KIND" = "comment-only" ]; then
  enforce_comment_scope "$diff_file"
fi

RESTORE_ON_FAIL=false

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
