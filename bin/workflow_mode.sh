#!/usr/bin/env bash
set -euo pipefail

mode="${WORKFLOW_MODE:-tactical}"
cmd="${1:-show}"
arg_mode="${2:-}"

is_valid_mode() {
  case "$1" in
    tactical|codex-assist|codex-investigate|codex-failure) return 0 ;;
    *) return 1 ;;
  esac
}

mode_description() {
  case "$1" in
    tactical) echo "Local-first tactical loop; Codex handoff disabled by default." ;;
    codex-assist) echo "Use Codex for bounded assistance while keeping checks scoped (offline=changed)." ;;
    codex-investigate) echo "Use Codex for deeper investigation and broader validation (offline=full)." ;;
    codex-failure) echo "Use Codex for hard failure analysis with broad local validation (offline=full)." ;;
  esac
}

print_mode() {
  is_valid_mode "$1" || {
    echo "INVALID mode: $1" >&2
    exit 1
  }
  echo "WORKFLOW_MODE=$1"
  echo "description: $(mode_description "$1")"
}

case "$cmd" in
  show)
    print_mode "$mode"
    ;;
  set)
    is_valid_mode "$arg_mode" || {
      echo "ERROR: set requires a valid mode" >&2
      exit 1
    }
    echo "export WORKFLOW_MODE=$arg_mode"
    ;;
  validate)
    is_valid_mode "$mode" || {
      echo "ERROR: invalid WORKFLOW_MODE=$mode" >&2
      exit 1
    }
    echo "PASS: WORKFLOW_MODE=$mode"
    ;;
  list)
    echo "tactical"
    echo "codex-assist"
    echo "codex-investigate"
    echo "codex-failure"
    ;;
  *)
    cat <<'USAGE' >&2
Usage:
  ./bin/workflow_mode.sh show
  ./bin/workflow_mode.sh validate
  ./bin/workflow_mode.sh list
  ./bin/workflow_mode.sh set <mode>

Modes:
  tactical
  codex-assist
  codex-investigate
  codex-failure
USAGE
    exit 1
    ;;
esac
