#!/bin/sh
set -eu

BASE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ALLOWLIST="$BASE_DIR/policies/remote-codex-allowlist.txt"
DENYLIST="$BASE_DIR/policies/remote-codex-denylist.txt"

TASK_FILE=""
OUT_DIR="$BASE_DIR/.remote-tasks"
TASK_NAME="remote-task"
INCLUDES=""

usage() {
  cat <<'USAGE'
Usage:
  ./bin/remote_prepare.sh --task-file <path> [--out-dir <path>] [--name <task-name>] --include <path> [--include <path> ...]

Notes:
  - Included files are checked against policies/remote-codex-denylist.txt and allowlist.
  - Output bundle includes sanitized file copies under context/.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --task-file)
      TASK_FILE="${2:-}"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --name)
      TASK_NAME="${2:-}"
      shift 2
      ;;
    --include)
      val="${2:-}"
      [ -n "$val" ] || { echo "ERROR: --include requires a value" >&2; exit 1; }
      INCLUDES="$INCLUDES
$val"
      shift 2
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

[ -n "$TASK_FILE" ] || { echo "ERROR: --task-file is required" >&2; exit 1; }
[ -f "$TASK_FILE" ] || { echo "ERROR: task file not found: $TASK_FILE" >&2; exit 1; }
[ -n "$INCLUDES" ] || { echo "ERROR: at least one --include is required" >&2; exit 1; }
[ -r "$ALLOWLIST" ] || { echo "ERROR: missing allowlist: $ALLOWLIST" >&2; exit 1; }
[ -r "$DENYLIST" ] || { echo "ERROR: missing denylist: $DENYLIST" >&2; exit 1; }

is_match_in_list() {
  target="$1"
  list_file="$2"
  matched=1
  while IFS= read -r pat || [ -n "$pat" ]; do
    case "$pat" in
      ''|\#*) continue ;;
    esac
    case "$target" in
      $pat)
        matched=0
        break
        ;;
    esac
  done <"$list_file"
  return "$matched"
}

sanitize_stream() {
  # Redact obvious secrets and direct IP-hosted URLs.
  sed -E \
    -e 's#([A-Za-z_][A-Za-z0-9_]*(TOKEN|PASS|PASSWORD|SECRET|API_KEY|KEY))=[^[:space:]]+#\1=<REDACTED>#g' \
    -e 's#(https?://)[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+#\1<REDACTED_IP>#g'
}

slug="$(printf '%s' "$TASK_NAME" | tr ' ' '-' | tr -cd '[:alnum:]_.-')"
[ -n "$slug" ] || slug="remote-task"
stamp="$(date +%Y%m%d_%H%M%S)"
bundle_dir="$OUT_DIR/${stamp}_${slug}"
context_dir="$bundle_dir/context"

mkdir -p "$context_dir"

manifest="$bundle_dir/manifest.txt"
instructions="$bundle_dir/instructions.md"

printf 'bundle: %s\ncreated: %s\n\n' "$bundle_dir" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$manifest"
printf '# Remote Task Instructions\n\n' >"$instructions"
printf 'Use only files from this bundle. Keep changes bounded and patch-oriented.\n\n' >>"$instructions"
printf '## Validation checklist\n- make quick\n- make test-changed-offline (or make test-offline when helper/test harness changes)\n' >>"$instructions"

# Copy task file as-is (author-controlled brief).
cp "$TASK_FILE" "$bundle_dir/task.md"

echo "$INCLUDES" | sed '/^$/d' | while IFS= read -r include_path; do
  rel="$include_path"
  case "$rel" in
    "$BASE_DIR"/*) rel="${rel#"$BASE_DIR"/}" ;;
  esac

  src="$BASE_DIR/$rel"
  [ -f "$src" ] || { echo "ERROR: include file not found: $rel" >&2; exit 1; }

  if is_match_in_list "$rel" "$DENYLIST"; then
    echo "ERROR: include file blocked by denylist: $rel" >&2
    exit 1
  fi

  allowed_note="allowlisted"
  if ! is_match_in_list "$rel" "$ALLOWLIST"; then
    allowed_note="not-allowlisted"
  fi

  dst="$context_dir/$rel"
  mkdir -p "$(dirname "$dst")"
  sanitize_stream <"$src" >"$dst"

  printf '%s\t%s\n' "$rel" "$allowed_note" >>"$manifest"
done

echo
echo "Bundle created: $bundle_dir"
echo "Task brief: $bundle_dir/task.md"
echo "Context dir: $context_dir"
echo "Manifest: $manifest"
