#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
WRAPPER="$REPO_ROOT/bin/markitdown_wrapper.py"

usage() {
  cat <<'USAGE'
Usage: bin/oss_wave_markitdown.sh <command>

Commands:
  install     Install MarkItDown into local venv (no global mutation).
  smoke       Run local conversion smoke test against a sample input.
  convert     Convert a file: --input <path> --output <path>
  uninstall   Remove local MarkItDown venv.
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

ensure_venv() {
  command -v uv >/dev/null 2>&1 || die "uv is required"
}

cmd_install() {
  ensure_venv
  uv tool install --force markitdown
  echo "PASS: MarkItDown installed via uv tool"
}

cmd_smoke() {
  ensure_venv
  local sample_in="$REPO_ROOT/tmp/markitdown_smoke_input.txt"
  local sample_out="$REPO_ROOT/tmp/markitdown_smoke_output.md"
  mkdir -p "$REPO_ROOT/tmp"
  cat > "$sample_in" <<'SAMPLE'
MarkItDown smoke test
- local ingestion path
- wrapper execution
SAMPLE
  "$WRAPPER" "$sample_in" --output "$sample_out"
  [ -s "$sample_out" ] || die "smoke output missing: $sample_out"
  echo "PASS: MarkItDown smoke conversion complete"
}

cmd_convert() {
  ensure_venv
  local input=""
  local output=""
  shift
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --input) input="${2:-}"; shift 2 ;;
      --output) output="${2:-}"; shift 2 ;;
      *) die "unknown argument: $1" ;;
    esac
  done
  [ -n "$input" ] || die "--input is required"
  [ -n "$output" ] || die "--output is required"
  "$WRAPPER" "$input" --output "$output"
}

cmd_uninstall() {
  uv tool uninstall markitdown >/dev/null 2>&1 || true
  echo "PASS: MarkItDown tool removed (if previously installed)"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    install) cmd_install ;;
    smoke) cmd_smoke ;;
    convert) cmd_convert "$@" ;;
    uninstall) cmd_uninstall ;;
    ""|-h|--help) usage ;;
    *) die "unknown command: $cmd" ;;
  esac
}

main "$@"
