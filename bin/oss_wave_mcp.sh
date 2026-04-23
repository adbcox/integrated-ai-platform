#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CONFIG="$REPO_ROOT/config/oss_wave/mcp_servers.json"

usage() {
  cat <<'USAGE'
Usage: bin/oss_wave_mcp.sh <command> [args]

Commands:
  list                         Show approved first-wave MCP servers.
  smoke                        Check npm registry availability for approved servers.
  launch <server-id> [--root PATH] [--dry-run]
                               Launch approved MCP server via governed wrapper.
  rollback                     Print rollback instructions.
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_jq() {
  command -v jq >/dev/null 2>&1 || die "jq is required"
}

server_pkg() {
  local server_id="$1"
  jq -r --arg id "$server_id" '.approved_servers[] | select(.id==$id) | .package' "$CONFIG"
}

cmd_list() {
  require_jq
  jq -r '.approved_servers[] | "- " + .id + " => " + .package + " (" + .risk_level + ")"' "$CONFIG"
}

cmd_smoke() {
  require_jq
  local failed=0
  local pkg_list
  pkg_list="$(mktemp "${TMPDIR:-/tmp}/mcp-pkgs.XXXXXX")"
  jq -r '.approved_servers[].package' "$CONFIG" >"$pkg_list"
  while IFS= read -r pkg; do
    if npm view "$pkg" name version >/dev/null 2>&1; then
      echo "PASS: npm package available: $pkg"
    else
      echo "FAIL: npm package unavailable: $pkg" >&2
      failed=1
    fi
  done <"$pkg_list"
  rm -f "$pkg_list"
  [ "$failed" -eq 0 ] || die "one or more MCP packages are unavailable"
}

cmd_launch() {
  require_jq
  local server_id="${2:-}"
  [ -n "$server_id" ] || die "server id is required"
  local pkg
  pkg="$(server_pkg "$server_id")"
  [ -n "$pkg" ] && [ "$pkg" != "null" ] || die "server not approved: $server_id"

  local dry_run=0
  local root="$REPO_ROOT"
  shift 2
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --dry-run) dry_run=1; shift ;;
      --root)
        root="${2:-}"
        shift 2
        ;;
      *) die "unknown argument: $1" ;;
    esac
  done

  local root_abs repo_abs
  repo_abs="$(cd "$REPO_ROOT" && pwd)"
  root_abs="$(cd "$root" && pwd)"
  case "$root_abs" in
    "$repo_abs"|"$repo_abs"/*) ;;
    *) die "--root must remain inside repo root: $repo_abs" ;;
  esac

  local args=""
  if [ "$server_id" = "filesystem" ]; then
    args=" \"$root_abs\""
  fi

  local cmd="npx -y $pkg$args"
  if [ "$dry_run" -eq 1 ]; then
    echo "[dry-run] $cmd"
    return 0
  fi

  # shellcheck disable=SC2086
  eval "$cmd"
}

cmd_rollback() {
  cat <<'TXT'
Rollback/disable:
1. Remove MCP entries from local MCP client config.
2. Stop any running server processes started by this wrapper.
3. Optionally remove npm cache entries for these servers.
TXT
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    list) cmd_list ;;
    smoke) cmd_smoke ;;
    launch) cmd_launch "$@" ;;
    rollback) cmd_rollback ;;
    ""|-h|--help) usage ;;
    *) die "unknown command: $cmd" ;;
  esac
}

main "$@"
