#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi
set -euo pipefail

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DEFAULT_OUT_ROOT="$BASE_DIR/artifacts/aider_runs/local"
OUT_ROOT="${AIDER_RUN_ROOT:-$DEFAULT_OUT_ROOT}"
ensure_out_root() {
  if mkdir -p "$OUT_ROOT" >/dev/null 2>&1; then
    local probe="$OUT_ROOT/.write_test.$$"
    if touch "$probe" >/dev/null 2>&1; then
      rm -f "$probe" >/dev/null 2>&1 || true
      return 0
    fi
  fi
  if [ -z "${AIDER_RUN_ROOT:-}" ]; then
    OUT_ROOT="/tmp/aider_runs/local"
    if mkdir -p "$OUT_ROOT" >/dev/null 2>&1; then
      local probe="$OUT_ROOT/.write_test.$$"
      if touch "$probe" >/dev/null 2>&1; then
        rm -f "$probe" >/dev/null 2>&1 || true
        echo "[aider-supervisor] WARN: falling back to $OUT_ROOT for artifact storage." >&2
        return 0
      fi
    fi
  fi
  echo "[aider-supervisor] ERROR: cannot create artifact root '$OUT_ROOT'" >&2
  exit 1
}
ensure_out_root

LABEL="${AIDER_SUP_LABEL:-fast}"
MODE="${AIDER_SUP_MODE:-fast}"
WRAP_TIMEOUT="${AIDER_SUP_WRAP_TIMEOUT:-${AIDER_SUP_TIMEOUT:-7200}}"
EXPECT_NO_EDIT="${AIDER_SUP_EXPECT_NO_EDIT:-0}"
VALIDATIONS_RAW="${AIDER_SUP_VALIDATIONS:-}"
CMD=("$@")
CWD="$PWD"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RUN_ID="${TIMESTAMP}_${LABEL}_$$"
OUT_DIR="$OUT_ROOT/$RUN_ID"
mkdir -p "$OUT_DIR"

capture_pre_state() {
  git status --porcelain=v1 --branch >"$OUT_DIR/pre_status.txt"
  git ls-files --others --exclude-standard >"$OUT_DIR/pre_untracked.txt" || true
}

capture_post_state() {
  git status --porcelain=v1 --branch >"$OUT_DIR/post_status.txt"
  git ls-files --others --exclude-standard >"$OUT_DIR/post_untracked.txt" || true
  git diff --stat >"$OUT_DIR/diff.stat" || true
  git diff --numstat >"$OUT_DIR/diff.numstat" || true
  git diff --name-only >"$OUT_DIR/diff.files" || true
  git diff >"$OUT_DIR/diff.patch" || true
}

detect_new_untracked() {
  sort "$OUT_DIR/pre_untracked.txt" >"$OUT_DIR/pre_untracked.sort"
  sort "$OUT_DIR/post_untracked.txt" >"$OUT_DIR/post_untracked.sort"
  comm -13 "$OUT_DIR/pre_untracked.sort" "$OUT_DIR/post_untracked.sort" \
    | grep -vE '^(artifacts/|tmp/|\\.aider/)' \
    | sed '/^$/d' >"$OUT_DIR/new_untracked.txt" || true
}

run_aider() {
  local log="$OUT_DIR/aider.log"
  local exit_code
  set +e
  if [ "${WRAP_TIMEOUT}" -gt 0 ]; then
    timeout --foreground "$WRAP_TIMEOUT" "${CMD[@]}" 2>&1 | tee "$log"
    exit_code=${PIPESTATUS[0]}
  else
    "${CMD[@]}" 2>&1 | tee "$log"
    exit_code=${PIPESTATUS[0]}
  fi
  set -e
  return "$exit_code"
}

run_validations() {
  local had_failure=0
  : >"$OUT_DIR/validation_results.tsv"
  if [ -n "$VALIDATIONS_RAW" ]; then
    local idx=1
    while IFS= read -r line || [ -n "$line" ]; do
      [ -n "$line" ] || continue
      local vlog="$OUT_DIR/validation-${idx}.log"
      echo "[aider-supervisor] running validation: $line"
      local start_ts
      start_ts=$(date +%s)
      set +e
      bash -c "$line" >"$vlog" 2>&1
      local code=$?
      set -e
      local duration
      duration=$(( $(date +%s) - start_ts ))
      printf '%s\t%d\t%d\t%s\n' "$line" "$code" "$duration" "${vlog#$BASE_DIR/}" >>"$OUT_DIR/validation_results.tsv"
      if [ "$code" -ne 0 ]; then
        had_failure=1
      fi
      idx=$((idx + 1))
    done <<<"$VALIDATIONS_RAW"
  fi
  return "$had_failure"
}

write_failure_signatures() {
  : >"$OUT_DIR/failure_signatures.txt"
  for sig in "$@"; do
    printf '%s\n' "$sig" >>"$OUT_DIR/failure_signatures.txt"
  done
}

build_metadata() {
  python3 - "$BASE_DIR" "$OUT_DIR" <<'PY'
import json, os, sys, pathlib
base = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
def rel(path):
    p = out / path
    if not p.exists():
        return ""
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)
def read_lines(path):
    p = out / path
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text().splitlines() if line.strip()]
def read_validations():
    p = out / "validation_results.tsv"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        cmd, code, duration, vlog = line.split('\t')
        rows.append({
            "command": cmd,
            "exit_code": int(code),
            "duration_sec": int(duration),
            "log": vlog
        })
    return rows
metadata = {
    "run_id": os.environ["RUN_ID"],
    "label": os.environ["LABEL"],
    "mode": os.environ["MODE"],
    "command": os.environ["CMD_STRING"],
    "cwd": os.environ["CWD_PATH"],
    "start_time": os.environ["START_TIME"],
    "duration_sec": int(os.environ["DURATION_SEC"]),
    "exit_code": int(os.environ["EXIT_CODE"]),
    "env": {
        "OLLAMA_API_BASE": os.environ.get("AIDER_SUP_API_BASE", os.environ.get("OLLAMA_API_BASE", "")),
        "MODEL": os.environ.get("AIDER_SUP_MODEL", ""),
        "MAP_TOKENS": os.environ.get("AIDER_SUP_MAP_TOKENS", ""),
        "TIMEOUT": os.environ.get("AIDER_SUP_TIMEOUT_FLAG", "")
    },
    "logs": {
        "aider": rel("aider.log")
    },
    "git": {
        "pre_status": rel("pre_status.txt"),
        "post_status": rel("post_status.txt"),
        "diff_stat": rel("diff.stat"),
        "diff_files": rel("diff.files"),
        "diff_patch": rel("diff.patch")
    },
    "new_untracked": read_lines("new_untracked.txt"),
    "failure_signatures": read_lines("failure_signatures.txt"),
    "validation_results": read_validations(),
    "status": os.environ["OVERALL_STATUS"]
}
print(json.dumps(metadata, indent=2))
PY
}

main() {
  capture_pre_state
  START_TIME="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  start_epoch="$(date +%s)"
  set +e
  run_aider
  EXIT_CODE="$?"
  set -e
  duration=$(( $(date +%s) - start_epoch ))
  capture_post_state
  detect_new_untracked
  validation_failed=0
  if ! run_validations; then
    validation_failed=1
  fi

  failure_signatures=()
  if [ "$EXIT_CODE" -eq 124 ]; then
    failure_signatures+=("timeout")
  fi
  if [ "$EXPECT_NO_EDIT" -eq 1 ] && [ -s "$OUT_DIR/diff.files" ]; then
    failure_signatures+=("no_edit_violation")
  fi
  if [ -s "$OUT_DIR/new_untracked.txt" ]; then
    failure_signatures+=("unexpected_file_creation")
  fi
  if [ "$validation_failed" -eq 1 ]; then
    failure_signatures+=("validation_failed")
  fi
  if [ "${failure_signatures+x}" = "x" ]; then
    write_failure_signatures "${failure_signatures[@]}" 2>/dev/null || true
  fi

  sig_count=0
  if [ "${failure_signatures+x}" = "x" ]; then
    sig_count="${#failure_signatures[@]}"
  fi
  if [ "$sig_count" -gt 0 ]; then
    OVERALL_STATUS="failed"
  elif [ "$EXIT_CODE" -ne 0 ]; then
    OVERALL_STATUS="failed"
  else
    OVERALL_STATUS="passed"
  fi

  CMD_STRING="$(printf '%q ' "${CMD[@]}")"
  export RUN_ID LABEL MODE CMD_STRING CWD_PATH="$CWD" START_TIME DURATION_SEC="$duration" EXIT_CODE OVERALL_STATUS
  build_metadata >"$OUT_DIR/metadata.json"

  if [ "$OVERALL_STATUS" = "failed" ] && [ "${AIDER_SUP_FAIL_FAST:-0}" -eq 1 ]; then
    exit 1
  fi
  exit "$EXIT_CODE"
}

main
