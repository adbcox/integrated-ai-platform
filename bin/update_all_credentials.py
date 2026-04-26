#!/usr/bin/env python3
"""Update docker/.env with all discovered credentials.

Usage:
    python3 bin/update_all_credentials.py                          # auto-discover everything
    python3 bin/update_all_credentials.py --dry-run               # show what would change
    python3 bin/update_all_credentials.py --opnsense-key K --opnsense-secret S
    python3 bin/update_all_credentials.py --plex-token TOKEN
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
ENV_FILE   = _REPO_ROOT / "docker" / ".env"


def _run_script(script: str) -> tuple[str, int]:
    """Run a discovery script, return (stdout+stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "bin" / script)],
        capture_output=True, text=True, timeout=60,
        cwd=str(_REPO_ROOT),
    )
    return (result.stdout + result.stderr).strip(), result.returncode


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def _write_env(updates: dict[str, str], dry_run: bool) -> None:
    content = ENV_FILE.read_text() if ENV_FILE.exists() else ""

    for key, value in updates.items():
        pattern = rf"^{re.escape(key)}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            content = content.rstrip("\n") + f"\n{replacement}\n"

    if dry_run:
        print("\n[DRY RUN] Would write to docker/.env:")
        for k, v in updates.items():
            display = v[:12] + "…" if len(v) > 16 else v
            print(f"  {k}={display}")
        return

    ENV_FILE.write_text(content)
    print(f"\n✓ Wrote {len(updates)} credential(s) to {ENV_FILE}")


def discover_plex(plex_token_override: str | None) -> dict[str, str]:
    updates: dict[str, str] = {}
    if plex_token_override:
        updates["PLEX_TOKEN"] = plex_token_override
        updates["PLEX_URL"]   = "http://192.168.10.201:32400"
        print(f"  ✓ Plex token (manual): {plex_token_override[:12]}…")
        return updates

    print("  Running discover_plex_token.py…")
    out, rc = _run_script("discover_plex_token.py")
    print(out)
    if rc == 0:
        m = re.search(r"^PLEX_TOKEN=(.+)$", out, re.MULTILINE)
        if m:
            updates["PLEX_TOKEN"] = m.group(1).strip()
            updates["PLEX_URL"]   = "http://192.168.10.201:32400"
            print(f"  ✓ Plex token discovered")
    else:
        print("  ⚠  Plex token not found — update PLEX_TOKEN manually")
    return updates


def discover_opnsense(key_override: str | None, secret_override: str | None) -> dict[str, str]:
    updates: dict[str, str] = {}
    if key_override and secret_override:
        updates["OPNSENSE_API_KEY"]    = key_override
        updates["OPNSENSE_API_SECRET"] = secret_override
        updates["OPNSENSE_URL"]        = "https://192.168.10.1"
        print(f"  ✓ OPNsense key (manual): {key_override[:12]}…")
        return updates

    print("  Running discover_opnsense_api.py…")
    out, rc = _run_script("discover_opnsense_api.py")
    print(out)
    if rc == 0:
        km = re.search(r"^OPNSENSE_API_KEY=(.+)$",    out, re.MULTILINE)
        sm = re.search(r"^OPNSENSE_API_SECRET=(.+)$", out, re.MULTILINE)
        if km and sm:
            updates["OPNSENSE_API_KEY"]    = km.group(1).strip()
            updates["OPNSENSE_API_SECRET"] = sm.group(1).strip()
            updates["OPNSENSE_URL"]        = "https://192.168.10.1"
            print("  ✓ OPNsense credentials discovered")
    else:
        print("  ⚠  OPNsense API key not found — see manual steps above")
    return updates


def seedbox_credentials() -> dict[str, str]:
    """Seedbox credentials — known configuration."""
    return {
        "SEEDBOX_HOST":     "193.163.71.22",
        "SEEDBOX_PORT":     "2088",
        "SEEDBOX_USER":     "seedit4me",
        "SEEDBOX_PASSWORD": "+Huckbear17",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Update docker/.env with all credentials")
    parser.add_argument("--dry-run",         action="store_true")
    parser.add_argument("--plex-token",      default="")
    parser.add_argument("--opnsense-key",    default="")
    parser.add_argument("--opnsense-secret", default="")
    parser.add_argument("--skip-plex",       action="store_true")
    parser.add_argument("--skip-opnsense",   action="store_true")
    parser.add_argument("--skip-seedbox",    action="store_true")
    args = parser.parse_args()

    if not ENV_FILE.exists():
        print(f"❌ {ENV_FILE} not found")
        return 1

    print(f"Updating {ENV_FILE}\n")
    all_updates: dict[str, str] = {}

    # 1. Plex
    if not args.skip_plex:
        print("── Plex ──────────────────────────────────")
        all_updates.update(discover_plex(args.plex_token or None))

    # 2. OPNsense
    if not args.skip_opnsense:
        print("\n── OPNsense ──────────────────────────────")
        all_updates.update(discover_opnsense(
            args.opnsense_key    or None,
            args.opnsense_secret or None,
        ))

    # 3. Seedbox (always — known good credentials)
    if not args.skip_seedbox:
        print("\n── Seedbox ───────────────────────────────")
        sb = seedbox_credentials()
        all_updates.update(sb)
        print(f"  ✓ Seedbox: {sb['SEEDBOX_USER']}@{sb['SEEDBOX_HOST']}:{sb['SEEDBOX_PORT']}")

    if not all_updates:
        print("\nNothing to update.")
        return 0

    _write_env(all_updates, dry_run=args.dry_run)

    if not args.dry_run:
        print("\nUpdated credentials summary:")
        for k, v in sorted(all_updates.items()):
            display = v[:12] + "…" if len(v) > 16 else v
            print(f"  {k:30s} = {display}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
