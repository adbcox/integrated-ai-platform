#!/bin/bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bin/aider_micro.sh "anchored message" path/to/file1 [path/to/file2]
  - Requires a clean working tree.
  - Limits micro tasks to at most two files.
  - Message must explicitly anchor each file using "<basename>::<token>" syntax.
  - Default supported class: single-file literal/comment wording replacements inside shell/bin files (see docs/safe-literal-probes.md).
  - Runs aider via bin/aider_local.sh and then make quick.
  - Fails if files outside the allowed list change or no file changes.
USAGE
}

RESTORE_ON_FAIL=false
LITERAL_FILE=""
LITERAL_OLD=""
LITERAL_NEW=""
LITERAL_BEFORE_FILE=""
LITERAL_FALLBACK_USED=false
WRITE_CHECK_COUNT=${AIDER_MICRO_WRITE_CHECKS:-3}
WRITE_CHECK_DELAY=${AIDER_MICRO_WRITE_DELAY_SEC:-1}

check_path_writable() {
  local path="$1"
  local label="$2"
  local attempt="$3"
  local total="$4"
  local probe
  probe="$path/.aider_micro_write_probe.$$.$RANDOM"
  if ! (umask 022 && printf 'probe\n' >"$probe" 2>/dev/null); then
    fail "repo $label path '$path' is not writable (attempt $attempt/$total); fix mount/permissions (e.g. remount rw, then rerun)." "repo_unwritable"
  fi
  rm -f "$probe" >/dev/null 2>&1 || true
}

ensure_repo_write_stable() {
  local repo_root
  repo_root=$(git rev-parse --show-toplevel)
  local git_dir="$repo_root/.git"
  local i
  for i in $(seq 1 "$WRITE_CHECK_COUNT"); do
    check_path_writable "$repo_root" "root" "$i" "$WRITE_CHECK_COUNT"
    check_path_writable "$git_dir" ".git" "$i" "$WRITE_CHECK_COUNT"
    if [ "$i" -lt "$WRITE_CHECK_COUNT" ]; then
      sleep "$WRITE_CHECK_DELAY"
    fi
  done
}

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

is_shell_like_path() {
  local f="$1"
  case "$f" in
    *.sh|shell/*|bin/*|operator_task.sh|start_*|run_*|update_*)
      return 0
      ;;
  esac
  return 1
}

guard_literal_shell_change() {
  local file="$1"
  if ! is_shell_like_path "$file"; then
    return
  fi
  local risky_regex='(\\b(set|if|then|fi|elif|else|for|while|until|case|esac|do|done|exit|return|trap)\\b|set[[:space:]]*-[[:alpha:]]+)'
  if printf '%s\n%s\n' "$LITERAL_OLD" "$LITERAL_NEW" | grep -qiE "$risky_regex"; then
    fail "literal replace touches shell control/strict-mode tokens in $file; use a wider lane" "literal_shell_risky"
  fi
}

literal_validate() {
  local target_file="$1"
  local snapshot="$2"
  if [ -z "$snapshot" ]; then
    return
  fi
  if ! LITERAL_FILE="$target_file" LITERAL_BEFORE_FILE="$snapshot" LITERAL_OLD="$LITERAL_OLD" LITERAL_NEW="$LITERAL_NEW" python3 - <<'PY'
import os, sys
from pathlib import Path

target_path = Path(os.environ['LITERAL_FILE'])
before_path = Path(os.environ['LITERAL_BEFORE_FILE'])
old = os.environ['LITERAL_OLD']
new = os.environ['LITERAL_NEW']

before = before_path.read_text()
after = target_path.read_text()

if old not in before:
    print("literal replace old text missing from snapshot", file=sys.stderr)
    sys.exit(1)

expected = before.replace(old, new, 1)
if before == expected:
    print("literal replace performed zero substitutions", file=sys.stderr)
    sys.exit(1)

if expected != after:
    print("literal replace produced unexpected diff", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
  then
    fail "literal replace produced unexpected changes" "literal_replace_diff"
  fi
}

literal_apply_direct() {
  local target_file="$1"
  local snapshot="$2"
  info "applying literal replace directly to $target_file"
  if ! LITERAL_FILE="$target_file" LITERAL_BEFORE_FILE="$snapshot" LITERAL_OLD="$LITERAL_OLD" LITERAL_NEW="$LITERAL_NEW" python3 - <<'PY'
import os, sys
from pathlib import Path

path = Path(os.environ['LITERAL_FILE'])
snapshot = Path(os.environ['LITERAL_BEFORE_FILE'])
old = os.environ['LITERAL_OLD']
new = os.environ['LITERAL_NEW']
text = path.read_text()
if old not in text:
    print(f"literal replace fallback: old text missing in {path}", file=sys.stderr)
    sys.exit(1)
updated = text.replace(old, new, 1)
if text == updated:
    print("literal replace fallback performed zero substitutions", file=sys.stderr)
    sys.exit(1)
path.write_text(updated)
sys.exit(0)
PY
  then
    fail "literal replace fallback could not apply change" "literal_replace_fallback"
  fi
  LITERAL_FALLBACK_USED=true
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
  if printf '%s' "$msg" | grep -Eq '<[[:space:][:alpha:][:digit:]_./-]+>' ; then
    fail "replace placeholder tokens like <OLD TEXT>/<anchor-token> with real text" "placeholder_prompt"
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
  elif printf '%s' "$msg_lower" | grep -q "replace exact text"; then
    detected_kind="literal-replace"
    local quote_count
    quote_count=$(printf "%s" "$msg" | tr -cd "'" | wc -c | tr -d ' ')
    if [ "$quote_count" -lt 4 ]; then
      fail "exact replace tasks must specify quoted old and new text" "literal_replace_contract"
    fi
    local parsed
    if ! parsed=$(MESSAGE="$msg" python3 - <<'PY'
import os,re,sys
text=os.environ['MESSAGE']
parts=re.findall(r"'([^']*)'", text)
if len(parts) < 2:
    sys.exit(1)
print(parts[0])
print(parts[1])
PY
); then
      fail "unable to parse literal replace old/new text" "literal_replace_contract"
    fi
    local literal_old literal_new
    literal_old=$(printf '%s\n' "$parsed" | sed -n '1p')
    literal_new=$(printf '%s\n' "$parsed" | sed -n '2p')
    if [ -z "$literal_new" ]; then
      fail "literal replace prompt must specify both old and new text" "literal_replace_contract"
    fi
    LITERAL_OLD="$literal_old"
    LITERAL_NEW="$literal_new"
    if [ "$LITERAL_OLD" = "$LITERAL_NEW" ]; then
      fail "literal replace old text matches new text" "literal_replace_contract"
    fi
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
ensure_repo_write_stable
ensure_message_quality "$MESSAGE"
ensure_allowed_files

if [ "$TASK_KIND" = "literal-replace" ]; then
  if [ ${#TARGET_FILES[@]} -ne 1 ]; then
    fail "literal replace tasks must specify exactly one file" "literal_replace_contract"
  fi
  LITERAL_FILE="${TARGET_FILES[0]}"
  if ! grep -F -- "$LITERAL_OLD" "$LITERAL_FILE" >/dev/null; then
    fail "literal replace old text not found in $LITERAL_FILE" "literal_replace_missing_old"
  fi
  guard_literal_shell_change "$LITERAL_FILE"
  LITERAL_BEFORE_FILE=$(mktemp)
  cp "$LITERAL_FILE" "$LITERAL_BEFORE_FILE"
fi

HEAD_BEFORE=$(git rev-parse HEAD)
TEST_MODE=false
if [ -n "${AIDER_MICRO_FAKE_DIFF_FILE:-}" ]; then
  TEST_MODE=true
fi

if [ "$TEST_MODE" = false ]; then
  RESTORE_ON_FAIL=true
  info "running aider on ${TARGET_FILES[*]}"
  if bash bin/aider_local.sh --message "$MESSAGE" "${TARGET_FILES[@]}"; then
    info "running quick validation"
    if ! PYTHONPYCACHEPREFIX=/tmp/aider_pycache make quick >/dev/null; then
      fail "make quick failed; inspect quick logs" "validation"
    fi
  else
    status=$?
    if [ "$status" -eq 0 ]; then
      status=99
    fi
    if [ "$TASK_KIND" = "literal-replace" ] && [ -n "$LITERAL_BEFORE_FILE" ]; then
      info "aider exit detected; attempting literal replace fallback"
      literal_apply_direct "$LITERAL_FILE" "$LITERAL_BEFORE_FILE"
      info "running quick validation after fallback"
      if ! PYTHONPYCACHEPREFIX=/tmp/aider_pycache make quick >/dev/null; then
        fail "make quick failed after fallback; inspect quick logs" "validation"
      fi
    else
      fail "aider exited non-zero (status $status). Inspect artifacts/aider_runs for details." "aider_exit" "$status"
    fi
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
cleanup() {
  rm -f "$diff_file"
  if [ -n "${LITERAL_BEFORE_FILE:-}" ]; then
    rm -f "$LITERAL_BEFORE_FILE"
  fi
}
trap cleanup EXIT

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
  if [ "$TASK_KIND" = "literal-replace" ] && [ "$LITERAL_FALLBACK_USED" = true ]; then
    info "no diff detected but literal fallback applied; treating as success"
  else
    fail "none of the target files changed" "no_change"
  fi
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

if [ "$TASK_KIND" = "literal-replace" ]; then
  literal_validate "$LITERAL_FILE" "$LITERAL_BEFORE_FILE"
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
