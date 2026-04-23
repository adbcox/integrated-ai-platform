#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="$REPO_ROOT/config/oss_wave/pr_agent.env"
ENV_TEMPLATE="$REPO_ROOT/config/oss_wave/pr_agent.env.example"

usage() {
  cat <<'USAGE'
Usage: bin/oss_wave_pr_agent.sh <command> [args]

Commands:
  install                       Install PR-Agent in local venv.
  validate-env                  Validate expected environment file and required keys.
  smoke                         Ensure executable is present and version responds.
  review --pr-url URL           Run local CLI review against a specific PR URL.
  rollback                      Disable local PR-Agent integration by removing env file.
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

ensure_venv() {
  command -v uv >/dev/null 2>&1 || die "uv is required"
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    set -a; . "$ENV_FILE"; set +a
  else
    die "missing $ENV_FILE (copy from $ENV_TEMPLATE)"
  fi
}

cmd_install() {
  ensure_venv
  uv tool install --force pr-agent
  echo "PASS: PR-Agent installed via uv tool"
}

cmd_validate_env() {
  load_env
  [ -n "${OPENAI_KEY:-}" ] || die "OPENAI_KEY is required"
  [ -n "${GITHUB_TOKEN:-}" ] || die "GITHUB_TOKEN is required"
  echo "PASS: PR-Agent env file validated"
}

cmd_smoke() {
  ensure_venv
  uvx --from pr-agent pr-agent --help >/dev/null
  echo "PASS: PR-Agent smoke checks complete"
}

cmd_review() {
  ensure_venv
  load_env
  shift
  local pr_url=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --pr-url)
        pr_url="${2:-}"
        shift 2
        ;;
      *) die "unknown argument: $1" ;;
    esac
  done
  [ -n "$pr_url" ] || die "--pr-url is required"
  OPENAI_KEY="$OPENAI_KEY" GITHUB_TOKEN="$GITHUB_TOKEN" \
    uvx --from pr-agent pr-agent --pr_url "$pr_url" review
}

cmd_rollback() {
  uv tool uninstall pr-agent >/dev/null 2>&1 || true
  rm -f "$ENV_FILE"
  echo "PASS: removed local PR-Agent env file and uninstalled tool if present"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    install) cmd_install ;;
    validate-env) cmd_validate_env ;;
    smoke) cmd_smoke ;;
    review) cmd_review "$@" ;;
    rollback) cmd_rollback ;;
    ""|-h|--help) usage ;;
    *) die "unknown command: $cmd" ;;
  esac
}

main "$@"
