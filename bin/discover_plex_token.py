#!/usr/bin/env python3
"""Auto-discover Plex authentication token from QNAP via SSH."""
from __future__ import annotations
import subprocess
import re
import sys
import os

QNAP_HOST = os.environ.get("QNAP_HOST", "192.168.10.201")
QNAP_USER = os.environ.get("QNAP_USER", "admin")
QNAP_PASS = os.environ.get("QNAP_PASS", "+Huckbear17")
QNAP_PORT = int(os.environ.get("QNAP_SSH_PORT", "22"))

PLEX_PATHS = [
    "/share/CACHEDEV2_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/Preferences.xml",
    "/share/CACHEDEV1_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/Preferences.xml",
    "/share/CACHEDEV3_DATA/.qpkg/PlexMediaServer/Library/Plex Media Server/Preferences.xml",
    "/share/.qpkg/PlexMediaServer/Library/Plex Media Server/Preferences.xml",
]


def _ssh_run(cmd: str) -> str:
    """Run a command on QNAP via paramiko, return stdout."""
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        QNAP_HOST, port=QNAP_PORT, username=QNAP_USER, password=QNAP_PASS,
        timeout=12, allow_agent=False, look_for_keys=False,
    )
    _, stdout, _ = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode(errors="replace")
    client.close()
    return out


def find_plex_token() -> str | None:
    print(f"Connecting to QNAP at {QNAP_USER}@{QNAP_HOST}:{QNAP_PORT}…")

    try:
        _ssh_run("echo CONNECTED")
        print("  SSH connection: OK")
    except Exception as e:
        print(f"  ❌ SSH failed: {e}")
        return None

    # Try known paths first
    for path in PLEX_PATHS:
        print(f"  Checking: {path}")
        try:
            content = _ssh_run(f'cat "{path}" 2>/dev/null')
            if content:
                m = re.search(r'PlexOnlineToken="([^"]+)"', content)
                if m:
                    print(f"  Found PlexOnlineToken")
                    return m.group(1)
                print(f"    File exists but no PlexOnlineToken")
        except Exception:
            pass

    # Dynamic search
    print("  Searching QNAP filesystem for Preferences.xml…")
    try:
        found = _ssh_run("find /share -name 'Preferences.xml' -path '*/Plex*' 2>/dev/null | head -5")
        for path in found.strip().splitlines():
            path = path.strip()
            if not path:
                continue
            print(f"  Trying: {path}")
            content = _ssh_run(f'cat "{path}" 2>/dev/null')
            m = re.search(r'PlexOnlineToken="([^"]+)"', content)
            if m:
                return m.group(1)
    except Exception as e:
        print(f"  find error: {e}")

    return None


def main() -> int:
    token = find_plex_token()
    if token:
        print(f"\nPLEX_TOKEN={token}")
        return 0

    print("\n❌ Could not auto-discover Plex token")
    print("\nManual fallback:")
    print(f"  ssh {QNAP_USER}@{QNAP_HOST}")
    print("  find /share -name 'Preferences.xml' -path '*/Plex*'")
    print("  grep PlexOnlineToken /path/to/Preferences.xml")
    return 1


if __name__ == "__main__":
    sys.exit(main())
