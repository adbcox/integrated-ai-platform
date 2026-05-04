#!/usr/bin/env bash
# FAILED BRANCH / HISTORICAL INSTALLER — DO NOT USE FOR NEW WORK
# D-17-72 disposition: retained for historical reference.
# This script installs a user-domain LaunchAgent (`~/Library/LaunchAgents`,
# `gui/<uid>` bootstrap + `launchctl load -w` fallback), which was superseded
# by D-17-51 headless doctrine after empirical bootstrap failures on this host.
# Canonical pattern: system-domain LaunchDaemons migration via
# `scripts/d-17-51-migrate-to-launchdaemons.sh`.
#
# Install + register the platform-registry launchd agent.
#
# Per Finding Y (D-17-28): the OS-upgrade-induced damage to the
# user-domain launchd registry can cause `bootstrap` and legacy `load -w`
# to silently fail. This script reports clearly when that happens so the
# operator can re-run after the Y-domain is repaired (typically a fresh
# login or reboot).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.iap.platform-registry.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.iap.platform-registry.plist"
LABEL="com.iap.platform-registry"

if [ ! -f "$PLIST_SRC" ]; then
    echo "ERROR: missing $PLIST_SRC" >&2
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST_SRC" "$PLIST_DST"
plutil -lint "$PLIST_DST"

# Try modern bootout/bootstrap path
launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true
if launchctl bootstrap "gui/$(id -u)" "$PLIST_DST" 2>/dev/null; then
    echo "OK: bootstrapped via gui/$(id -u)"
else
    # Legacy fallback
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    if launchctl load -w "$PLIST_DST" 2>/dev/null; then
        echo "OK: loaded via legacy launchctl load -w"
    else
        echo "WARN: launchctl load failed silently (likely Finding Y — user"
        echo "      launchd domain damaged by OS upgrade). Plist is installed"
        echo "      at $PLIST_DST and will load on next login or after the"
        echo "      user-domain is repaired."
    fi
fi

# Verify
if launchctl list | grep -q "$LABEL"; then
    echo "VERIFIED: $LABEL is registered"
    launchctl list | grep "$LABEL"
else
    echo "NOT REGISTERED yet — see warning above. Plist on disk: $PLIST_DST"
    exit 2
fi
