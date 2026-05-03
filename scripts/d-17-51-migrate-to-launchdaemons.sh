#!/usr/bin/env bash
# D-17-51 — migrate headless-safe com.iap LaunchAgents to LaunchDaemons.
# Runs in system domain, but each daemon runs as admin via UserName.
#
# Usage (single sudo invocation):
#   sudo /Users/admin/repos/integrated-ai-platform/scripts/d-17-51-migrate-to-launchdaemons.sh

set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "ERROR: run as root (sudo)." >&2
  exit 64
fi

AGENT_DIR="/Users/admin/Library/LaunchAgents"
DAEMON_DIR="/Library/LaunchDaemons"
LOG_DIR="/Users/admin/Library/Logs/iap"

mkdir -p "$DAEMON_DIR" "$LOG_DIR"
chown admin:staff "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Labels that require GUI/session interaction and should stay as LaunchAgent.
EXCLUDE_LABELS=(
  "com.iap.d-17-27-reminder"
)

python3 - <<'PY'
import glob, os, plistlib
AGENT_DIR='/Users/admin/Library/LaunchAgents'
DAEMON_DIR='/Library/LaunchDaemons'
LOG_DIR='/Users/admin/Library/Logs/iap'
EXCLUDE={'com.iap.d-17-27-reminder'}

for src in sorted(glob.glob(os.path.join(AGENT_DIR,'com.iap*.plist'))):
    with open(src,'rb') as f:
        d=plistlib.load(f)
    label=d.get('Label',os.path.basename(src).replace('.plist',''))
    if label in EXCLUDE:
        print(f'SKIP {label} gui-dependent')
        continue

    # Agent->daemon conversion
    d['UserName']='admin'
    d['GroupName']='staff'

    # Remove session-bound keys if present
    for k in ('LimitLoadToSessionType','AssociatedBundleIdentifiers'):
        d.pop(k,None)

    # Route daemon stdout/stderr to canonical log dir
    d['StandardOutPath']=f'{LOG_DIR}/{label}.out.log'
    d['StandardErrorPath']=f'{LOG_DIR}/{label}.err.log'

    # Normalize legacy heartbeat/log path from ~/.platform-logs to ~/Library/Logs/iap
    pa=d.get('ProgramArguments')
    if isinstance(pa,list) and len(pa)>=3 and pa[1]=='-c' and isinstance(pa[2],str):
        pa[2]=pa[2].replace('/Users/admin/.platform-logs','/Users/admin/Library/Logs/iap')
        d['ProgramArguments']=pa

    dst=os.path.join(DAEMON_DIR, os.path.basename(src))
    with open(dst,'wb') as f:
        plistlib.dump(d,f,sort_keys=False)
    print(f'WRITE {label} -> {dst}')
PY

# Ownership/permissions required by launchd for LaunchDaemons
for p in "$DAEMON_DIR"/com.iap*.plist; do
  [ -f "$p" ] || continue
  chown root:wheel "$p"
  chmod 644 "$p"

done

# Bootstrap in system domain
ok=0
fail=0
for p in "$DAEMON_DIR"/com.iap*.plist; do
  [ -f "$p" ] || continue
  label=$(plutil -extract Label raw -o - "$p" 2>/dev/null || basename "$p" .plist)
  if [ "$label" = "com.iap.d-17-27-reminder" ]; then
    continue
  fi
  launchctl bootout "system/$label" >/dev/null 2>&1 || true
  if launchctl bootstrap system "$p" >/dev/null 2>&1; then
    launchctl enable "system/$label" >/dev/null 2>&1 || true
    launchctl kickstart -k "system/$label" >/dev/null 2>&1 || true
    echo "OK   $label"
    ok=$((ok+1))
  else
    echo "FAIL $label"
    fail=$((fail+1))
  fi
done

echo "summary ok=$ok fail=$fail"
if [ "$fail" -ne 0 ]; then
  exit 67
fi

exit 0
