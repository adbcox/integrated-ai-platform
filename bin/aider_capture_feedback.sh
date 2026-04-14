#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DETECT="$BASE_DIR/bin/detect_changed_files.sh"
LEGACY_OUT_ROOT="$BASE_DIR/.local-model-data"
ESCALATION_ROOT="${ESCALATION_ROOT:-$BASE_DIR/artifacts/escalations}"
INDEX_FILE="$ESCALATION_ROOT/index.jsonl"
TASK_NAME=""
SUMMARY_FILE=""
OUTCOME_FILE=""
CHECKS_FILE=""
TASK_ID=""
WORKFLOW_MODE="${WORKFLOW_MODE:-tactical}"
ESCALATION_TRIGGER=""
PROBLEM_STATEMENT=""
CONSTRAINTS_TEXT=""
PLAN_SUMMARY=""
FIX_PATTERN=""
LOCAL_HEURISTIC=""
COMPLETION_SUMMARY=""
FORCE_ESCALATION_CAPTURE=0

usage() {
  cat <<'USAGE'
Usage (Stage-3 production lane default flow):
  ./bin/aider_capture_feedback.sh --name <task-name> [options]

Options (most-used subset, Stage-3 safe):
  --summary <path>                 Markdown summary file (Stage-3 capture)
  --outcome <path>                 Outcome file
  --checks <path>                  Commands/checks file
  --task-id <id>                   Explicit task id (default: timestamp+slug)
  --workflow-mode <mode>           tactical|codex-assist|codex-investigate|codex-failure
  --escalation-trigger <text>      Why Codex escalation was used
  --problem <text>                 Concise problem summary
  --constraints <text>             Constraint summary
  --plan-summary <text>            Codex plan summary
  --fix-pattern <text>             Fix pattern/root-cause classification
  --heuristic <text>               Reusable local-first heuristics
  --completion-summary <text>      Brief completion summary
  --force-escalation-capture       Write escalation artifacts even while in tactical mode

Creates the following artifacts:
- legacy local feedback record stored under .local-model-data/
- escalation artifacts for non-tactical workflows (or forced mode):
  artifacts/escalations/<task_id>/summary.json
  artifacts/escalations/<task_id>/timeline.log
  artifacts/escalations/<task_id>/patch-notes.md
  artifacts/escalations/index.jsonl
USAGE
}

json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e ':a;N;$!ba;s/\n/\\n/g'
}

json_array_from_file() {
  in_file="$1"
  first=1
  printf '['
  if [ -f "$in_file" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      [ -n "$line" ] || continue
      esc="$(json_escape "$line")"
      if [ "$first" -eq 0 ]; then
        printf ','
      fi
      printf '"%s"' "$esc"
      first=0
    done < "$in_file"
  fi
  printf ']'
}

timeline_log() {
  timeline_path="$1"
  shift
  printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >>"$timeline_path"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --summary)
      SUMMARY_FILE="${2:-}"
      shift 2
      ;;
    --outcome)
      OUTCOME_FILE="${2:-}"
      shift 2
      ;;
    --checks)
      CHECKS_FILE="${2:-}"
      shift 2
      ;;
    --task-id)
      TASK_ID="${2:-}"
      shift 2
      ;;
    --workflow-mode)
      WORKFLOW_MODE="${2:-}"
      shift 2
      ;;
    --escalation-trigger)
      ESCALATION_TRIGGER="${2:-}"
      shift 2
      ;;
    --problem)
      PROBLEM_STATEMENT="${2:-}"
      shift 2
      ;;
    --constraints)
      CONSTRAINTS_TEXT="${2:-}"
      shift 2
      ;;
    --plan-summary)
      PLAN_SUMMARY="${2:-}"
      shift 2
      ;;
    --fix-pattern)
      FIX_PATTERN="${2:-}"
      shift 2
      ;;
    --heuristic)
      LOCAL_HEURISTIC="${2:-}"
      shift 2
      ;;
    --completion-summary)
      COMPLETION_SUMMARY="${2:-}"
      shift 2
      ;;
    --force-escalation-capture)
      FORCE_ESCALATION_CAPTURE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

[ -x "$DETECT" ] || { echo "ERROR: missing helper: $DETECT" >&2; exit 1; }
[ -n "$TASK_NAME" ] || { echo "ERROR: --name flag is required" >&2; exit 1; }

case "$WORKFLOW_MODE" in
  tactical|codex-assist|codex-investigate|codex-failure) ;;
  *)
    echo "ERROR: invalid --workflow-mode (expected tactical|codex-assist|codex-investigate|codex-failure): $WORKFLOW_MODE" >&2
    exit 1
    ;;
esac

slug="$(printf '%s' "$TASK_NAME" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
[ -n "$slug" ] || slug="task"
ts="$(date +%Y%m%d_%H%M%S)"
if [ -z "$TASK_ID" ]; then
  TASK_ID="${ts}_${slug}"
fi

timestamp_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
repo="$BASE_DIR"
branch="$(git -C "$BASE_DIR" symbolic-ref --short -q HEAD || echo unknown)"

legacy_record_dir="$LEGACY_OUT_ROOT/$TASK_ID"
mkdir -p "$legacy_record_dir"

changed_files_tmp="$(mktemp)"
commands_tmp="$(mktemp)"
trap 'rm -f "$changed_files_tmp" "$commands_tmp"' EXIT HUP INT TERM

"$DETECT" | sed '/^$/d' | sort -u >"$changed_files_tmp"

if [ -n "$SUMMARY_FILE" ] && [ -f "$SUMMARY_FILE" ]; then
  cp "$SUMMARY_FILE" "$legacy_record_dir/summary.md"
else
  cat >"$legacy_record_dir/summary.md" <<'EOS'
# Summary
<note what changed and why>
EOS
fi

if [ -n "$OUTCOME_FILE" ] && [ -f "$OUTCOME_FILE" ]; then
  cp "$OUTCOME_FILE" "$legacy_record_dir/outcome.md"
else
  cat >"$legacy_record_dir/outcome.md" <<'EOS'
# Outcome
- status: partial
- key regressions prevented:
  - <key item>
- follow-ups (record next steps):
  - <follow-up item>
EOS
fi

if [ -n "$CHECKS_FILE" ] && [ -f "$CHECKS_FILE" ]; then
  cp "$CHECKS_FILE" "$legacy_record_dir/checks.txt"
else
  cat >"$legacy_record_dir/checks.txt" <<'EOS'
make quick
make test-changed-offline
EOS
fi

cp "$changed_files_tmp" "$legacy_record_dir/changed_files.txt"
cat >"$legacy_record_dir/meta.txt" <<EOS
task_id: $TASK_ID
task_name: $TASK_NAME
created_utc: $timestamp_utc
repo: $repo
branch: $branch
workflow_mode: $WORKFLOW_MODE
EOS

# Build escalation structure only for explicit Codex escalations unless forced.
if [ "$WORKFLOW_MODE" = "tactical" ] && [ "$FORCE_ESCALATION_CAPTURE" -ne 1 ] && [ -z "$ESCALATION_TRIGGER" ]; then
  echo "Saved local feedback record under: $legacy_record_dir"
  echo "Skipped escalation artifact capture (workflow_mode=tactical) by default."
  exit 0
fi

mkdir -p "$ESCALATION_ROOT/$TASK_ID"
summary_json_path="$ESCALATION_ROOT/$TASK_ID/summary.json"
timeline_path="$ESCALATION_ROOT/$TASK_ID/timeline.log"
patch_notes_path="$ESCALATION_ROOT/$TASK_ID/patch-notes.md"

if [ -z "$ESCALATION_TRIGGER" ]; then
  case "$WORKFLOW_MODE" in
    codex-assist) ESCALATION_TRIGGER="bounded-assist" ;;
    codex-investigate) ESCALATION_TRIGGER="complex-investigation" ;;
    codex-failure) ESCALATION_TRIGGER="hard-failure-analysis" ;;
    *) ESCALATION_TRIGGER="manual" ;;
  esac
fi

if [ -z "$PROBLEM_STATEMENT" ]; then
  PROBLEM_STATEMENT="$TASK_NAME"
fi

if [ -z "$CONSTRAINTS_TEXT" ]; then
  CONSTRAINTS_TEXT="Keep changes low-risk, machine-neutral, and avoid destructive operations."
fi

if [ -z "$PLAN_SUMMARY" ]; then
  PLAN_SUMMARY="Apply mode-driven Codex escalation, run local checks, and capture reusable outcomes."
fi

outcome_status="partial"
if [ -f "$legacy_record_dir/outcome.md" ]; then
  outcome_status_line="$(grep -E 'status:' "$legacy_record_dir/outcome.md" | head -n 1 || true)"
  case "$outcome_status_line" in
    *pass*) outcome_status="pass" ;;
    *fail*) outcome_status="fail" ;;
    *partial*) outcome_status="partial" ;;
  esac
fi

if [ -z "$FIX_PATTERN" ]; then
  FIX_PATTERN="unknown"
fi

if [ -z "$LOCAL_HEURISTIC" ]; then
  case "$WORKFLOW_MODE" in
    codex-failure)
      LOCAL_HEURISTIC="When repeated failures persist after one local attempt, escalate earlier with full test context."
      ;;
    codex-investigate)
      LOCAL_HEURISTIC="Escalate cross-file ambiguity after first local decomposition pass, then reuse resolved decomposition pattern locally."
      ;;
    codex-assist)
      LOCAL_HEURISTIC="Use local-first edits for straightforward changes; escalate only for bounded reasoning bottlenecks."
      ;;
    *)
      LOCAL_HEURISTIC="Prefer local-first execution and only escalate when complexity materially blocks progress."
      ;;
  esac
fi

if [ -z "$COMPLETION_SUMMARY" ]; then
  COMPLETION_SUMMARY="Captured escalation outcome and local reuse heuristic for future local-first handling."
fi

cp "$legacy_record_dir/checks.txt" "$commands_tmp"

files_json="$(json_array_from_file "$changed_files_tmp")"
commands_json="$(json_array_from_file "$commands_tmp")"
outcome_notes="$(cat "$legacy_record_dir/outcome.md" 2>/dev/null || true)"

{
  printf '{\n'
  printf '  "task_id": "%s",\n' "$(json_escape "$TASK_ID")"
  printf '  "timestamp_utc": "%s",\n' "$(json_escape "$timestamp_utc")"
  printf '  "repo": "%s",\n' "$(json_escape "$repo")"
  printf '  "branch": "%s",\n' "$(json_escape "$branch")"
  printf '  "workflow_mode": "%s",\n' "$(json_escape "$WORKFLOW_MODE")"
  printf '  "files_touched": %s,\n' "$files_json"
  printf '  "escalation_trigger": "%s",\n' "$(json_escape "$ESCALATION_TRIGGER")"
  printf '  "problem_statement": "%s",\n' "$(json_escape "$PROBLEM_STATEMENT")"
  printf '  "constraints": "%s",\n' "$(json_escape "$CONSTRAINTS_TEXT")"
  printf '  "codex_plan_summary": "%s",\n' "$(json_escape "$PLAN_SUMMARY")"
  printf '  "commands_tests_run": %s,\n' "$commands_json"
  printf '  "pass_fail_outcomes": "%s",\n' "$(json_escape "$outcome_status")"
  printf '  "outcome_notes": "%s",\n' "$(json_escape "$outcome_notes")"
  printf '  "fix_pattern_root_cause": "%s",\n' "$(json_escape "$FIX_PATTERN")"
  printf '  "reusable_local_first_heuristic": "%s",\n' "$(json_escape "$LOCAL_HEURISTIC")"
  printf '  "completion_summary": "%s"\n' "$(json_escape "$COMPLETION_SUMMARY")"
  printf '}\n'
} >"$summary_json_path"

: >"$timeline_path"
timeline_log "$timeline_path" "capture_started task_id=$TASK_ID"
timeline_log "$timeline_path" "workflow_mode=$WORKFLOW_MODE trigger=$ESCALATION_TRIGGER"
timeline_log "$timeline_path" "branch=$branch outcome=$outcome_status"
timeline_log "$timeline_path" "files_touched_count=$(sed '/^$/d' "$changed_files_tmp" | wc -l | tr -d ' ')"
timeline_log "$timeline_path" "capture_completed"

{
  echo "# Patch Notes"
  echo
  echo "- task_id: $TASK_ID"
  echo "- workflow_mode: $WORKFLOW_MODE"
  echo "- escalation_trigger: $ESCALATION_TRIGGER"
  echo "- branch: $branch"
  echo "- completion_status: $outcome_status"
  echo
  echo "## Problem"
  echo "$PROBLEM_STATEMENT"
  echo
  echo "## Plan Summary"
  echo "$PLAN_SUMMARY"
  echo
  echo "## Files Touched"
  sed '/^$/d;s/^/- /' "$changed_files_tmp"
  echo
  echo "## Commands / Tests Run"
  sed '/^$/d;s/^/- /' "$commands_tmp"
  echo
  echo "## Outcome"
  cat "$legacy_record_dir/outcome.md"
  echo
  echo "## Reusable Local-First Heuristic"
  echo "$LOCAL_HEURISTIC"
} >"$patch_notes_path"

mkdir -p "$ESCALATION_ROOT"
index_line=$(printf '{"task_id":"%s","timestamp_utc":"%s","repo":"%s","branch":"%s","workflow_mode":"%s","escalation_trigger":"%s","pass_fail_outcomes":"%s","summary_json":"%s"}' \
  "$(json_escape "$TASK_ID")" \
  "$(json_escape "$timestamp_utc")" \
  "$(json_escape "$repo")" \
  "$(json_escape "$branch")" \
  "$(json_escape "$WORKFLOW_MODE")" \
  "$(json_escape "$ESCALATION_TRIGGER")" \
  "$(json_escape "$outcome_status")" \
  "$(json_escape "$summary_json_path")")
printf '%s\n' "$index_line" >>"$INDEX_FILE"

echo "Captured local feedback record at: $legacy_record_dir"
echo "Captured escalation record: $ESCALATION_ROOT/$TASK_ID"
