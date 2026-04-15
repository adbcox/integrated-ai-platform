#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS_ROOT="${REPOS_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
BROWSER_OPERATOR_REPO="${BROWSER_OPERATOR_REPO:-${REPOS_ROOT}/platform-browser-operator}"
CONTROL_PLANE_REPO="${CONTROL_PLANE_REPO:-${REPOS_ROOT}/control-plane}"
EXPECTED_BRANCH="${EXPECTED_BRANCH:-main}"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"
REQUIRED_TOOLS_DEFAULT=(bash git sed awk python3 aider ollama)

augment_path_for_user_site_bins() {
  local py_bin_root="${HOME}/Library/Python"
  local candidate
  if [[ -d "$py_bin_root" ]]; then
    for candidate in "$py_bin_root"/*/bin; do
      [[ -d "$candidate" ]] || continue
      case ":${PATH}:" in
        *":${candidate}:"*) ;;
        *) PATH="${candidate}:${PATH}" ;;
      esac
    done
    export PATH
  fi
}

if [[ -n "${REQUIRED_TOOLS:-}" ]]; then
  # shellcheck disable=SC2206
  REQUIRED_TOOLS_LIST=(${REQUIRED_TOOLS})
else
  REQUIRED_TOOLS_LIST=("${REQUIRED_TOOLS_DEFAULT[@]}")
fi

pass() { printf 'PASS: %s\n' "$1"; }
warn() { printf 'WARN: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

require_repo() {
  local label="$1"
  local repo_path="$2"

  [[ -d "$repo_path" ]] || fail "${label}: repo path missing: ${repo_path}"
  pass "${label}: repo path exists (${repo_path})"

  git -C "$repo_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "${label}: not a valid git repo"
  pass "${label}: valid git repo"

  local branch
  branch="$(git -C "$repo_path" symbolic-ref --short -q HEAD || true)"
  [[ -n "$branch" ]] || fail "${label}: detached HEAD or no explicit branch"
  pass "${label}: explicit branch detected (${branch})"

  if [[ "$branch" != "$EXPECTED_BRANCH" ]]; then
    fail "${label}: expected branch '${EXPECTED_BRANCH}' but found '${branch}'"
  fi
  pass "${label}: expected branch matches (${EXPECTED_BRANCH})"

  local status_file
  status_file="${repo_path}/docs/repo-normalization-status.md"
  [[ -f "$status_file" ]] || fail "${label}: missing docs/repo-normalization-status.md"
  pass "${label}: normalization status doc present"

  grep -q '^- normalization_mode: intentional-local-baseline$' "$status_file" || \
    fail "${label}: normalization status doc missing expected normalization_mode"
  pass "${label}: normalization mode is intentional-local-baseline"

  local porcelain
  porcelain="$(git -C "$repo_path" status --porcelain)"
  if [[ -z "$porcelain" ]]; then
    pass "${label}: working tree clean"
  else
    if [[ "$ALLOW_DIRTY" == "1" ]]; then
      warn "${label}: working tree not clean; ALLOW_DIRTY=1 set"
      git -C "$repo_path" status --short --branch | sed -n '1,60p'
    else
      printf '%s\n' "$porcelain" | sed -n '1,40p' >&2
      fail "${label}: working tree not clean (set ALLOW_DIRTY=1 to acknowledge temporarily)"
    fi
  fi
}

check_tools() {
  local tool
  for tool in "${REQUIRED_TOOLS_LIST[@]}"; do
    command -v "$tool" >/dev/null 2>&1 || fail "required tool missing: ${tool}"
    pass "tool available: ${tool}"
  done
}

printf '=== Preflight Normalization Guard ===\n'
printf 'REPOS_ROOT=%s\n' "$REPOS_ROOT"
printf 'EXPECTED_BRANCH=%s\n' "$EXPECTED_BRANCH"
printf 'ALLOW_DIRTY=%s\n' "$ALLOW_DIRTY"

augment_path_for_user_site_bins
check_tools
require_repo "platform-browser-operator" "$BROWSER_OPERATOR_REPO"
require_repo "control-plane" "$CONTROL_PLANE_REPO"

printf 'PASS: preflight normalization guard complete\n'
