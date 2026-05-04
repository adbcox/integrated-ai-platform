#!/usr/bin/env bash
# FAILED BRANCH — user-domain LaunchAgent approach abandoned per
# D-17-51 RESOLUTION_PLAN (2026-05-03).
# Canonical pattern is LaunchDaemon in system domain:
#   scripts/d-17-51-migrate-to-launchdaemons.sh
# Do not reuse this script for new work.
#
# D-17-51 WP-05 operator-run script.
# Canonical headless bootstrap: user/<uid> domain (not gui/<uid>).
#
# Usage (single sudo invocation preferred):
#   sudo /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-launchagents-bootstrap-user-domain.sh

set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 64
fi

REPO_ROOT="/Users/admin/repos/integrated-ai-platform"
REPO_PLISTS_DIR="$REPO_ROOT/docker/launchd-agents"
USER_HOME="/Users/admin"
USER_PLISTS_DIR="$USER_HOME/Library/LaunchAgents"

# Prefer sudo-origin uid; fallback to admin uid 502 for this platform.
TARGET_UID="${SUDO_UID:-502}"

if ! id -u admin >/dev/null 2>&1; then
  echo "ERROR: expected admin user missing" >&2
  exit 65
fi

mkdir -p "$USER_PLISTS_DIR"

# Sync all repo com.iap plists into LaunchAgents (authoritative source).
shopt -s nullglob
repo_plists=("$REPO_PLISTS_DIR"/com.iap*.plist)
if [ ${#repo_plists[@]} -eq 0 ]; then
  echo "ERROR: no com.iap plists found in $REPO_PLISTS_DIR" >&2
  exit 66
fi

for src in "${repo_plists[@]}"; do
  dst="$USER_PLISTS_DIR/$(basename "$src")"
  install -m 0644 "$src" "$dst"
  chown admin:staff "$dst"
  echo "synced $(basename "$dst")"
done

# Build target set from installed LaunchAgents (includes legacy non-repo plists).
installed_plists=("$USER_PLISTS_DIR"/com.iap*.plist)

bootstrap_ok=0
bootstrap_fail=0

for plist in "${installed_plists[@]}"; do
  label=$(plutil -extract Label raw -o - "$plist" 2>/dev/null || basename "$plist" .plist)

  # Reversible cycle: bootout old registration if present, then bootstrap fresh.
  launchctl bootout "user/$TARGET_UID/$label" >/dev/null 2>&1 || true

  if launchctl bootstrap "user/$TARGET_UID" "$plist" >/dev/null 2>&1; then
    launchctl enable "user/$TARGET_UID/$label" >/dev/null 2>&1 || true
    launchctl kickstart -k "user/$TARGET_UID/$label" >/dev/null 2>&1 || true
    echo "OK   $label"
    bootstrap_ok=$((bootstrap_ok+1))
  else
    echo "FAIL $label"
    bootstrap_fail=$((bootstrap_fail+1))
  fi
done

echo "summary ok=$bootstrap_ok fail=$bootstrap_fail uid=$TARGET_UID"

if [ $bootstrap_fail -ne 0 ]; then
  echo "ERROR: one or more agents failed bootstrap" >&2
  exit 67
fi

exit 0
