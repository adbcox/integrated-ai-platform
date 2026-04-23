#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CONFIG_DIR="$REPO_ROOT/config/oss_wave"
ENV_TEMPLATE="$CONFIG_DIR/openhands.env.example"
ENV_FILE="$CONFIG_DIR/openhands.env"

usage() {
  cat <<'USAGE'
Usage: bin/oss_wave_openhands.sh <command> [--dry-run]

Commands:
  prereqs          Validate launch prerequisites and show approved launch modes.
  validate-config  Validate required OpenHands configuration variables.
  launch-gui       Launch local GUI mode (docker) with governed workspace mount.
  launch-headless  Launch headless mode (docker) with governed workspace mount.
  rollback         Disable OpenHands integration posture for this repo.
  smoke            Run bounded smoke checks (no long-running server).

Notes:
  - Copy config/oss_wave/openhands.env.example to config/oss_wave/openhands.env
  - Launch modes are intentionally wrapper-bound to avoid architecture drift.
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

DRY_RUN=0
if [ "${2:-}" = "--dry-run" ] || [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

run_cmd() {
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] $*"
    return 0
  fi
  "$@"
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    set -a; . "$ENV_FILE"; set +a
  else
    echo "WARN: missing $ENV_FILE; using template defaults where possible." >&2
  fi

  : "${OPENHANDS_MODE:=docker}"
  : "${OPENHANDS_IMAGE:=docker.openhands.dev/openhands/openhands:latest}"
  : "${OPENHANDS_RUNTIME_IMAGE:=docker.openhands.dev/openhands/runtime:0.59-nikolaik}"
  : "${OPENHANDS_PORT:=3000}"
  : "${OPENHANDS_WORKSPACE_DIR:=$REPO_ROOT}"
  : "${OPENHANDS_STATE_DIR:=$REPO_ROOT/.local-model-data/openhands-state}"
  : "${LLM_MODEL:=qwen2.5-coder:14b}"
  : "${LLM_BASE_URL:=http://host.docker.internal:11434/v1}"
  : "${LLM_API_KEY:=ollama-placeholder}"
  case "$LLM_MODEL" in
    */*) LLM_MODEL_RESOLVED="$LLM_MODEL" ;;
    *) LLM_MODEL_RESOLVED="openai/$LLM_MODEL" ;;
  esac
  case "$OPENHANDS_WORKSPACE_DIR" in
    /*) ;;
    *) OPENHANDS_WORKSPACE_DIR="$REPO_ROOT/$OPENHANDS_WORKSPACE_DIR" ;;
  esac
  case "$OPENHANDS_STATE_DIR" in
    /*) ;;
    *) OPENHANDS_STATE_DIR="$REPO_ROOT/$OPENHANDS_STATE_DIR" ;;
  esac
}

assert_workspace_boundary() {
  local canonical_root canonical_workspace
  canonical_root="$(cd "$REPO_ROOT" && pwd)"
  canonical_workspace="$(cd "$OPENHANDS_WORKSPACE_DIR" && pwd)"
  case "$canonical_workspace" in
    "$canonical_root"|"$canonical_root"/*) ;;
    *) die "OPENHANDS_WORKSPACE_DIR must stay inside repo root: $canonical_root" ;;
  esac
}

cmd_prereqs() {
  echo "Approved launch modes:"
  echo "  - launch-gui: docker local GUI"
  echo "  - launch-headless: docker headless mode"
  command -v docker >/dev/null 2>&1 || die "docker is required for current approved launch modes"
  echo "PASS: docker is available"
}

cmd_validate_config() {
  load_env
  assert_workspace_boundary
  [ "$OPENHANDS_MODE" = "docker" ] || die "OPENHANDS_MODE must be 'docker' for this first wave"
  [ -n "$OPENHANDS_IMAGE" ] || die "OPENHANDS_IMAGE is required"
  [ -n "$OPENHANDS_RUNTIME_IMAGE" ] || die "OPENHANDS_RUNTIME_IMAGE is required"
  [ -n "$OPENHANDS_PORT" ] || die "OPENHANDS_PORT is required"
  [ -n "$OPENHANDS_STATE_DIR" ] || die "OPENHANDS_STATE_DIR is required"
  [ -n "$LLM_MODEL" ] || die "LLM_MODEL is required"
  [ -n "$LLM_BASE_URL" ] || die "LLM_BASE_URL is required"
  [ -n "$LLM_API_KEY" ] || die "LLM_API_KEY is required (placeholder allowed)"
  mkdir -p "$OPENHANDS_STATE_DIR"
  echo "PASS: OpenHands config validated"
}

cmd_launch_gui() {
  load_env
  assert_workspace_boundary
  mkdir -p "$OPENHANDS_STATE_DIR"
  run_cmd docker run --rm -it \
    -p "$OPENHANDS_PORT:3000" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e LLM_MODEL="$LLM_MODEL_RESOLVED" \
    -e LLM_BASE_URL="$LLM_BASE_URL" \
    -e LLM_API_KEY="$LLM_API_KEY" \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE="$OPENHANDS_RUNTIME_IMAGE" \
    -v "$OPENHANDS_WORKSPACE_DIR:/opt/workspace" \
    -v "$OPENHANDS_STATE_DIR:/opt/openhands/.openhands-state" \
    "$OPENHANDS_IMAGE"
}

cmd_launch_headless() {
  load_env
  assert_workspace_boundary
  mkdir -p "$OPENHANDS_STATE_DIR"
  run_cmd docker run --rm -i \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e LLM_MODEL="$LLM_MODEL_RESOLVED" \
    -e LLM_BASE_URL="$LLM_BASE_URL" \
    -e LLM_API_KEY="$LLM_API_KEY" \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE="$OPENHANDS_RUNTIME_IMAGE" \
    -v "$OPENHANDS_WORKSPACE_DIR:/workspace" \
    -v "$OPENHANDS_STATE_DIR:/opt/openhands/.openhands-state" \
    "$OPENHANDS_IMAGE" \
    python -m openhands.core.main \
    -t "${OPENHANDS_TASK:-Sanity check: list files in the repository and summarize the structure}" \
    -d /workspace
}

cmd_smoke() {
  cmd_validate_config
  if command -v docker >/dev/null 2>&1; then
    run_cmd docker image inspect "${OPENHANDS_IMAGE}" >/dev/null 2>&1 || \
      echo "INFO: image not present locally yet: ${OPENHANDS_IMAGE}" >&2
  else
    echo "WARN: docker unavailable; launch smoke deferred" >&2
  fi
  echo "PASS: OpenHands smoke checks complete"
}

cmd_rollback() {
  if [ -f "$ENV_FILE" ]; then
    rm -f "$ENV_FILE"
    echo "Removed $ENV_FILE"
  fi
  echo "OpenHands wrappers remain present but disabled without env file."
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    prereqs) cmd_prereqs ;;
    validate-config) cmd_validate_config ;;
    launch-gui) cmd_launch_gui ;;
    launch-headless) cmd_launch_headless ;;
    smoke) cmd_smoke ;;
    rollback) cmd_rollback ;;
    ""|-h|--help) usage ;;
    --dry-run) usage ;;
    *) die "unknown command: $cmd" ;;
  esac
}

main "${1:-}"
