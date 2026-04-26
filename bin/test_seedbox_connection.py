#!/usr/bin/env python3
"""Validate connectivity to all media services: Seedbox, Plex, OPNsense, Flood.

Usage:
    python3 bin/test_seedbox_connection.py [--host HOST] [--port PORT]
                                           [--user USER] [--password PASS]
                                           [--plex-url URL] [--plex-token TOKEN]
                                           [--opnsense-url URL]
                                           [--opnsense-key KEY] [--opnsense-secret SECRET]
"""
from __future__ import annotations

import argparse
import base64
import datetime
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Defaults (env overrides)
# ---------------------------------------------------------------------------
DEFAULT_HOST     = os.environ.get("SEEDBOX_HOST",         "193.163.71.22")
DEFAULT_PORT     = int(os.environ.get("SEEDBOX_PORT",     "2088"))
DEFAULT_USER     = os.environ.get("SEEDBOX_USER",         "seedit4me")
DEFAULT_PASSWORD = os.environ.get("SEEDBOX_PASSWORD",     "+Huckbear17")

DEFAULT_PLEX_URL   = os.environ.get("PLEX_URL",   "http://192.168.10.201:32400")
DEFAULT_PLEX_TOKEN = os.environ.get("PLEX_TOKEN", "")

DEFAULT_OPNSENSE_URL    = os.environ.get("OPNSENSE_URL",        "https://192.168.10.1")
DEFAULT_OPNSENSE_KEY    = os.environ.get("OPNSENSE_API_KEY",    "")
DEFAULT_OPNSENSE_SECRET = os.environ.get("OPNSENSE_API_SECRET", "")

PROBE_DIRS = [
    "/home/seedit4me",
    "/home/seedit4me/torrents/rtorrent",
    "/home/seedit4me/rwatch",
]

CONNECT_TIMEOUT = 10
FLOOD_PORT      = 3000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(label: str, ok: bool, detail: str = "") -> bool:
    symbol = "✓" if ok else "✗"
    line = f"  [{symbol}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)
    return ok


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def _fmt_bytes(n: int) -> str:
    if n >= 1024**3:
        return f"{n / 1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n / 1024**2:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n} B"


def _age_str(age_hours: float) -> str:
    if age_hours < 1:
        return f"{int(age_hours * 60)}m ago"
    if age_hours < 48:
        return f"{age_hours:.1f}h ago"
    return f"{age_hours / 24:.1f}d ago"


# ---------------------------------------------------------------------------
# Seedbox SFTP / SSH checks
# ---------------------------------------------------------------------------

def check_sftp_connect(host: str, port: int, user: str, password: str) -> Tuple[bool, Any]:
    """Try to connect via SFTP. Returns (ok, client_or_error_msg)."""
    try:
        import paramiko
    except ImportError:
        return False, "paramiko not installed (pip install paramiko)"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            allow_agent=False,
            look_for_keys=False,
            timeout=CONNECT_TIMEOUT,
        )
        return True, client
    except Exception as e:
        return False, str(e)


def list_dir(sftp, path: str) -> List[Dict]:
    """List a remote directory. Returns list of file dicts or []."""
    try:
        attrs = sftp.listdir_attr(path)
    except Exception:
        return []

    now = datetime.datetime.now().timestamp()
    files = []
    for a in attrs:
        if a.filename.startswith("."):
            continue
        mtime = a.st_mtime or 0
        age_h = (now - mtime) / 3600
        size  = a.st_size or 0
        is_d  = bool(a.st_mode and (a.st_mode & 0o40000))
        files.append({
            "name":       a.filename,
            "size":       size,
            "age_hours":  age_h,
            "modified":   datetime.datetime.fromtimestamp(mtime).isoformat() if mtime else "",
            "is_dir":     is_d,
            "is_active":  a.filename.endswith(".part") or age_h < (5 / 60),
        })
    return sorted(files, key=lambda x: x["modified"], reverse=True)


def check_directories(client) -> None:
    _section("Seedbox — Directory Listings")
    sftp = client.open_sftp()

    for path in PROBE_DIRS:
        print(f"\n  Dir: {path}")
        entries = list_dir(sftp, path)

        non_dir = [f for f in entries if not f["is_dir"]]
        dirs    = [f for f in entries if f["is_dir"]]
        active  = [f for f in non_dir if f["is_active"]]
        total_bytes = sum(f["size"] for f in non_dir)

        _check(
            "listdir OK",
            True,
            f"{len(non_dir)} files, {len(dirs)} subdirs, "
            f"total {_fmt_bytes(total_bytes)}, {len(active)} active",
        )
        for f in non_dir[:5]:
            active_tag = " [ACTIVE]" if f["is_active"] else ""
            print(
                f"      {f['name']:<50}  {_fmt_bytes(f['size']):>10}  "
                f"{_age_str(f['age_hours'])}{active_tag}"
            )
        if len(non_dir) > 5:
            print(f"      … and {len(non_dir) - 5} more files")

    sftp.close()


def check_rclone(client) -> None:
    _section("Seedbox — rclone")
    try:
        _, stdout, stderr = client.exec_command("rclone version", timeout=10)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        if out:
            _check("rclone installed", True, out.splitlines()[0])
        else:
            _check("rclone installed", False, err[:120] or "no output")
    except Exception as e:
        _check("rclone installed", False, str(e)[:120])


# ---------------------------------------------------------------------------
# Flood check
# ---------------------------------------------------------------------------

def check_flood(host: str) -> None:
    _section("Flood Web UI")
    url = f"http://{host}:{FLOOD_PORT}/api/auth/verify"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            _check("Flood reachable", True, f"HTTP {r.status} at {url}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _check("Flood reachable", True, f"HTTP 401 (auth required) — Flood is running")
        else:
            _check("Flood reachable", False, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        _check("Flood reachable", False, f"Connection failed: {e.reason}")
    except Exception as e:
        _check("Flood reachable", False, str(e)[:100])


# ---------------------------------------------------------------------------
# Plex check
# ---------------------------------------------------------------------------

def check_plex(plex_url: str, plex_token: str) -> None:
    _section("Plex Media Server")

    if not plex_token:
        _check("Plex token configured", False, "PLEX_TOKEN not set — run update_all_credentials.py")
        return

    _check("Plex token configured", True, f"{plex_token[:8]}…")

    # Test server identity
    identity_url = f"{plex_url}/identity?X-Plex-Token={plex_token}"
    try:
        req = urllib.request.Request(identity_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            import json
            data = json.loads(r.read())
            machine_id = data.get("MediaContainer", {}).get("machineIdentifier", "unknown")
            version    = data.get("MediaContainer", {}).get("version", "unknown")
            _check("Plex reachable", True, f"server={machine_id[:16]} v{version}")
    except urllib.error.HTTPError as e:
        _check("Plex reachable", False, f"HTTP {e.code}")
        return
    except Exception as e:
        _check("Plex reachable", False, str(e)[:120])
        return

    # Test library count
    libs_url = f"{plex_url}/library/sections?X-Plex-Token={plex_token}"
    try:
        req2 = urllib.request.Request(libs_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req2, timeout=10) as r2:
            import json
            data2 = json.loads(r2.read())
            libs = data2.get("MediaContainer", {}).get("Directory", [])
            lib_names = [lib.get("title", "?") for lib in libs]
            _check("Plex libraries", True, f"{len(libs)} libraries: {', '.join(lib_names[:5])}")
    except Exception as e:
        _check("Plex libraries", False, str(e)[:120])


# ---------------------------------------------------------------------------
# OPNsense check
# ---------------------------------------------------------------------------

def check_opnsense(opnsense_url: str, api_key: str, api_secret: str) -> None:
    _section("OPNsense Firewall")
    import ssl

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE

    if not api_key or not api_secret:
        _check("OPNsense credentials configured", False,
               "OPNSENSE_API_KEY/SECRET not set — see bin/discover_opnsense_api.py --help")
        # Try unauthenticated ping at least
        try:
            req = urllib.request.Request(f"{opnsense_url}/api/core/firmware/info",
                                         headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                _check("OPNsense reachable (unauth)", True, f"HTTP {r.status} at {opnsense_url}")
        except Exception as e:
            _check("OPNsense reachable (unauth)", False, str(e)[:120])
        return

    _check("OPNsense credentials configured", True, f"key={api_key[:8]}…")

    # Test firmware info endpoint with Basic auth
    creds  = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    fw_url = f"{opnsense_url}/api/core/firmware/info"
    try:
        req = urllib.request.Request(fw_url, headers={
            "Accept":        "application/json",
            "Authorization": f"Basic {creds}",
        })
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            import json
            data = json.loads(r.read())
            version = data.get("product_version", "unknown")
            _check("OPNsense API auth", True, f"version={version}")
    except urllib.error.HTTPError as e:
        _check("OPNsense API auth", False, f"HTTP {e.code} — check API key/secret")
        return
    except Exception as e:
        _check("OPNsense API auth", False, str(e)[:120])
        return

    # Test gateway status
    gw_url = f"{opnsense_url}/api/routes/gateway/status"
    try:
        req2 = urllib.request.Request(gw_url, headers={
            "Accept":        "application/json",
            "Authorization": f"Basic {creds}",
        })
        with urllib.request.urlopen(req2, context=ctx, timeout=10) as r2:
            import json
            gw_data = json.loads(r2.read())
            items = gw_data.get("items", [])
            _check("OPNsense gateway status", True, f"{len(items)} gateways")
    except Exception as e:
        _check("OPNsense gateway status", False, str(e)[:120])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Multi-service connectivity validator")
    p.add_argument("--host",             default=DEFAULT_HOST,            help="Seedbox hostname or IP")
    p.add_argument("--port",             default=DEFAULT_PORT,            type=int, help="Seedbox SSH port")
    p.add_argument("--user",             default=DEFAULT_USER,            help="Seedbox SSH username")
    p.add_argument("--password",         default=DEFAULT_PASSWORD,        help="Seedbox SSH password")
    p.add_argument("--plex-url",         default=DEFAULT_PLEX_URL,        help="Plex server URL")
    p.add_argument("--plex-token",       default=DEFAULT_PLEX_TOKEN,      help="Plex auth token")
    p.add_argument("--opnsense-url",     default=DEFAULT_OPNSENSE_URL,    help="OPNsense base URL")
    p.add_argument("--opnsense-key",     default=DEFAULT_OPNSENSE_KEY,    help="OPNsense API key")
    p.add_argument("--opnsense-secret",  default=DEFAULT_OPNSENSE_SECRET, help="OPNsense API secret")
    p.add_argument("--skip-seedbox",     action="store_true",             help="Skip seedbox SFTP tests")
    p.add_argument("--skip-plex",        action="store_true",             help="Skip Plex tests")
    p.add_argument("--skip-opnsense",    action="store_true",             help="Skip OPNsense tests")
    p.add_argument("--skip-flood",       action="store_true",             help="Skip Flood tests")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    results: list[bool] = []

    # ── Seedbox ──────────────────────────────────────────────────────────────
    if not args.skip_seedbox:
        print(f"\nSeedbox: {args.user}@{args.host}:{args.port}")
        _section("Seedbox — SSH/SFTP Connection")
        ok, result = check_sftp_connect(args.host, args.port, args.user, args.password)
        results.append(ok)
        if not ok:
            _check("SFTP connect", False, str(result))
            print("  Cannot proceed with directory checks — skipping.")
        else:
            _check("SFTP connect", True, f"authenticated as {args.user}@{args.host}:{args.port}")
            client = result
            try:
                check_directories(client)
                check_rclone(client)
            finally:
                client.close()

    # ── Flood ─────────────────────────────────────────────────────────────────
    if not args.skip_flood:
        check_flood(args.host)

    # ── Plex ──────────────────────────────────────────────────────────────────
    if not args.skip_plex:
        check_plex(args.plex_url, args.plex_token)

    # ── OPNsense ──────────────────────────────────────────────────────────────
    if not args.skip_opnsense:
        check_opnsense(args.opnsense_url, args.opnsense_key, args.opnsense_secret)

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("Done")
    print("  Review [✓]/[✗] lines above for full details.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
