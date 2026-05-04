#!/usr/bin/env bash
# D-17-58 — install Mac Studio Ollama LaunchDaemon from repo-tracked plist.
#
# Run from macmini (operator workstation):
#   /Users/admin/repos/integrated-ai-platform/scripts/install-ollama-launchdaemon-mac-studio.sh
#
# This script executes all privileged steps remotely on mac-studio.internal.

set -euo pipefail

REPO_PLIST="/Users/admin/repos/integrated-ai-platform/docker/launchd-agents/com.iap.ollama.plist"
REMOTE_HOST="mac-studio.internal"
REMOTE_TMP="/tmp/com.iap.ollama.plist"
REMOTE_DST="/Library/LaunchDaemons/com.iap.ollama.plist"

if [ ! -f "$REPO_PLIST" ]; then
  echo "ERROR: plist missing at $REPO_PLIST" >&2
  exit 64
fi

# Copy plist to remote temp path as admin user.
scp "$REPO_PLIST" "${REMOTE_HOST}:${REMOTE_TMP}"

# Privileged install/bootstrap on remote.
ssh "$REMOTE_HOST" "sudo /bin/bash -s" <<'REMOTE_EOF'
set -euo pipefail

TMP_PLIST="/tmp/com.iap.ollama.plist"
DST_PLIST="/Library/LaunchDaemons/com.iap.ollama.plist"
LOG_DIR="/Users/admin/Library/Logs/iap"
LABEL="com.iap.ollama"

if [ ! -f "$TMP_PLIST" ]; then
  echo "ERROR: remote temp plist missing: $TMP_PLIST" >&2
  exit 65
fi

mkdir -p "$LOG_DIR"
chown admin:staff "$LOG_DIR"
chmod 755 "$LOG_DIR"

install -m 0644 "$TMP_PLIST" "$DST_PLIST"
chown root:wheel "$DST_PLIST"

# Reversible cycle: unload prior, then bootstrap fresh.
launchctl bootout "system/$LABEL" >/dev/null 2>&1 || true
launchctl bootstrap system "$DST_PLIST"
launchctl enable "system/$LABEL" >/dev/null 2>&1 || true
launchctl kickstart -k "system/$LABEL"

# Verification snapshot.
launchctl print "system/$LABEL" | awk '/state =|pid =|last exit code =/{print}'
REMOTE_EOF

# Read-only remote API proof from host network.
curl -sS "http://192.168.10.142:11434/api/tags" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("models:", len(d.get("models", [])))'

echo "Install complete: com.iap.ollama on mac-studio.internal"
