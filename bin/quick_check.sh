#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DETECT="$BASE_DIR/bin/detect_changed_files.sh"
PY_CACHE_PREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/quick_pycache}"
mkdir -p "$PY_CACHE_PREFIX" 2>/dev/null || true

check_shell=1
check_python=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --shell-only)
      check_shell=1
      check_python=0
      shift
      ;;
    --python-only)
      check_shell=0
      check_python=1
      shift
      ;;
    --all)
      check_shell=1
      check_python=1
      shift
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

if [ ! -x "$DETECT" ]; then
  echo "ERROR: missing helper: $DETECT" >&2
  exit 1
fi

changed_files="$("$DETECT" "$@")"
changed_file_list="$(mktemp "${TMPDIR:-/tmp}/quick-check.changed.XXXXXX")"
cleanup() {
  rm -f "$changed_file_list"
}
trap cleanup EXIT INT TERM
printf '%s\n' "$changed_files" >"$changed_file_list"

shell_checked=0
python_checked=0

echo "[quick] Reviewing files selected for default Stage-3 quick checks..."
if [ -z "$changed_files" ]; then
  echo "[quick] No changed files detected for default Stage-3 quick checks."
  exit 0
fi

while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    .compat-archive/*|.rename-backups/*|.host-backups/*|*.bak.*|*.bad_*|qnap_*.sh)
      continue
      ;;
  esac
  if [ ! -f "$BASE_DIR/$f" ]; then
    continue
  fi
  case "$f" in
    bin/aider_local.sh|bin/aider_micro.sh|bin/aider_failure_supervisor.sh)
      [ "$check_shell" -eq 1 ] || continue
      bash -n "$BASE_DIR/$f"
      echo "OK: shell syntax (bash) $f"
      shell_checked=1
      ;;
    *.sh)
      [ "$check_shell" -eq 1 ] || continue
      sh -n "$BASE_DIR/$f"
      echo "OK: shell syntax $f"
      shell_checked=1
      ;;
    *.py)
      [ "$check_python" -eq 1 ] || continue
      PYTHONPYCACHEPREFIX="$PY_CACHE_PREFIX" python3 -m py_compile "$BASE_DIR/$f"
      echo "OK: python syntax $f"
      python_checked=1
      ;;
  esac
done <"$changed_file_list"

# If shared helper changed, run shell helper smoke checks.
if [ "$check_shell" -eq 1 ] && grep -Fx "shell/common.sh" "$changed_file_list" >/dev/null 2>&1; then
  echo "[quick] shell/common.sh changed; running Stage-3 helper smoke tests..."
  sh -c '. "$1"; extract_session_id "{\"session_id\":\"abc-123\"}"' sh "$BASE_DIR/shell/common.sh" >/dev/null
  sh -c '. "$1"; extract_session_id "Using session: abc-123"' sh "$BASE_DIR/shell/common.sh" >/dev/null
  sh -c '. "$1"; require_exec sh' sh "$BASE_DIR/shell/common.sh" >/dev/null
  echo "OK: helper smoke tests complete"
fi

if [ "$shell_checked" -eq 0 ] && [ "$python_checked" -eq 0 ]; then
  echo "[quick] No shell/python files to check (Stage-3 skip)."
  exit 0
fi

echo "[quick] PASS: Stage-3 quick checks complete (shell/python syntax checks verified)."
