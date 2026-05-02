#!/usr/bin/env python3
"""17.I — OPNsense API client (Unbound overrides + health).

Reads `secret/opnsense/api` (fields: api_key, api_secret, host) via the
`opnsense-api-reader` Vault AppRole and exposes two functions used by
drift detection (D-16-06 + 17.I):

    opnsense_get_unbound_overrides() -> list[dict]
        Each row: {"hostname": str, "domain": str, "fqdn": str,
                   "ip": str, "rr": str, "enabled": bool, "uuid": str}
    opnsense_health() -> dict
        {"ok": bool, "vault_ok": bool, "api_ok": bool,
         "override_count": int|None, "error": str|None}

Credentials are loaded via the AppRole (NOT the root token) so this
script can be run from cron/launchd without exposing privileged tokens.
Errors never include credential values.

Stdlib only — no `hvac`, no `requests` — so pre-commit + CI can
run it without a venv.

Smoke check (`python3 opnsense_client.py --smoke`) at the bottom of
this file mirrors the run-locally pattern from cross-index-validate.py.

Module name uses underscores (snake_case) so it's importable from
check-repo-coherence.py; CLI invocation also works (`./opnsense_client.py`).
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.request
from base64 import b64encode
from pathlib import Path
from urllib.error import HTTPError, URLError

VAULT_CONTAINER = "vault-server"
VAULT_ADDR_INTERNAL = "http://127.0.0.1:8200"
APPROLE_DIR = Path.home() / ".vault-approle" / "opnsense-api-reader"
ROLE_ID_FILE = APPROLE_DIR / "role-id"
SECRET_ID_FILE = APPROLE_DIR / "secret-id"
DOCKER_BIN = "/opt/homebrew/bin/docker"

OPNSENSE_TIMEOUT_SEC = 10


class OPNsenseClientError(RuntimeError):
    """Raised for any client-level failure. Messages never carry credentials."""


def _docker_exec_vault(vault_token: str, args: list[str]) -> str:
    """Run a `vault` command inside the vault-server container.
    Returns stdout. Raises OPNsenseClientError on non-zero exit.
    Token is passed via env, never via argv.
    """
    cmd = [
        DOCKER_BIN, "exec",
        "-e", f"VAULT_TOKEN={vault_token}",
        "-e", f"VAULT_ADDR={VAULT_ADDR_INTERNAL}",
        VAULT_CONTAINER, "vault",
    ] + args
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as exc:
        # Strip stderr aggressively — Vault errors can echo paths/tokens
        err = (exc.stderr or "").strip().splitlines()
        safe = err[0] if err else "(no stderr)"
        raise OPNsenseClientError(f"vault command failed: {safe}") from None


def _approle_login() -> str:
    """Exchange role-id + secret-id for a short-lived Vault token."""
    if not ROLE_ID_FILE.is_file() or not SECRET_ID_FILE.is_file():
        raise OPNsenseClientError(
            f"AppRole creds missing under {APPROLE_DIR}. "
            "Run T1 of 17.I to provision."
        )
    role_id = ROLE_ID_FILE.read_text().strip()
    secret_id = SECRET_ID_FILE.read_text().strip()
    cmd = [
        DOCKER_BIN, "exec",
        "-e", f"VAULT_ADDR={VAULT_ADDR_INTERNAL}",
        VAULT_CONTAINER, "vault", "write", "-field=token",
        "auth/approle/login",
        f"role_id={role_id}",
        f"secret_id={secret_id}",
    ]
    try:
        token = subprocess.check_output(
            cmd, text=True, stderr=subprocess.PIPE
        ).strip()
    except subprocess.CalledProcessError:
        # Don't surface stderr — could echo the secret_id we just sent
        raise OPNsenseClientError("AppRole login failed") from None
    if not token:
        raise OPNsenseClientError("AppRole login returned empty token")
    return token


def _load_credentials() -> tuple[str, str, str]:
    """Returns (api_key, api_secret, host). Logs in via AppRole each call;
    caller should batch operations within one credential lifetime if
    repeated calls become a hot path."""
    token = _approle_login()
    key = _docker_exec_vault(
        token, ["kv", "get", "-field=api_key", "secret/opnsense/api"]
    )
    secret = _docker_exec_vault(
        token, ["kv", "get", "-field=api_secret", "secret/opnsense/api"]
    )
    host = _docker_exec_vault(
        token, ["kv", "get", "-field=host", "secret/opnsense/api"]
    )
    if not key or not secret or not host:
        raise OPNsenseClientError(
            "OPNsense credentials incomplete — secret/opnsense/api must "
            "have api_key, api_secret, host fields"
        )
    return key, secret, host


def _opnsense_get(
    key: str, secret: str, host: str, path: str, timeout: int = OPNSENSE_TIMEOUT_SEC
) -> dict:
    """HTTP GET against the OPNsense API. Returns parsed JSON.
    Verifies TLS by default-disabled (LAN-internal self-signed cert)."""
    if not path.startswith("/"):
        path = "/" + path
    url = f"https://{host}{path}"
    auth = b64encode(f"{key}:{secret}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # LAN-internal self-signed cert
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read().decode()
    except HTTPError as exc:
        raise OPNsenseClientError(
            f"OPNsense API HTTP {exc.code} on {path}"
        ) from None
    except URLError as exc:
        # exc.reason might be a socket error — safe to surface
        raise OPNsenseClientError(
            f"OPNsense API unreachable on {path}: {exc.reason}"
        ) from None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise OPNsenseClientError(
            f"OPNsense API returned non-JSON on {path} ({len(body)} bytes)"
        ) from None


def opnsense_get_unbound_overrides() -> list[dict]:
    """Returns Unbound host overrides as a list of normalized dicts.

    Endpoint: /api/unbound/settings/searchHostOverride
    Source row keys (probed 2026-05-01):
        hostname, domain, server, rr, enabled, uuid, aliases, description,
        ttl, mx, mxprio, txtdata, addptr, isAlias, %rr

    Returned shape (subset, normalized):
        {"hostname": "plane", "domain": "internal",
         "fqdn": "plane.internal", "ip": "192.168.10.145",
         "rr": "A", "enabled": True, "uuid": "..."}
    """
    key, secret, host = _load_credentials()
    payload = _opnsense_get(
        key, secret, host, "/api/unbound/settings/searchHostOverride"
    )
    rows = payload.get("rows", [])
    out: list[dict] = []
    for r in rows:
        hostname = (r.get("hostname") or "").strip()
        domain = (r.get("domain") or "").strip()
        fqdn = f"{hostname}.{domain}" if hostname else domain
        out.append({
            "hostname": hostname,
            "domain": domain,
            "fqdn": fqdn,
            "ip": (r.get("server") or "").strip(),
            "rr": (r.get("rr") or "").strip(),
            "enabled": str(r.get("enabled") or "0") == "1",
            "uuid": r.get("uuid", ""),
        })
    return out


def opnsense_health() -> dict:
    """Returns connectivity + auth status without raising.
    Suitable for status-file pattern (D-16-06)."""
    result = {
        "ok": False, "vault_ok": False, "api_ok": False,
        "override_count": None, "error": None,
    }
    try:
        key, secret, host = _load_credentials()
        result["vault_ok"] = True
    except OPNsenseClientError as exc:
        result["error"] = f"vault: {exc}"
        return result
    try:
        payload = _opnsense_get(
            key, secret, host, "/api/unbound/settings/searchHostOverride"
        )
        result["api_ok"] = True
        result["override_count"] = int(payload.get("total", 0))
        result["ok"] = True
    except OPNsenseClientError as exc:
        result["error"] = f"api: {exc}"
    return result


def _smoke() -> int:
    """Smoke check — exercise both functions; print a short summary."""
    print("== opnsense_health() ==")
    h = opnsense_health()
    print(json.dumps(h, indent=2))
    if not h["ok"]:
        return 1
    print()
    print("== opnsense_get_unbound_overrides() (first 5) ==")
    rows = opnsense_get_unbound_overrides()
    print(f"Total: {len(rows)}")
    for r in rows[:5]:
        print(f"  {r['fqdn']:40s} -> {r['ip']:18s} {r['rr']:5s} en={r['enabled']}")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="opnsense_client",
        description="OPNsense API client — Unbound overrides + health.",
    )
    sub = p.add_subparsers(dest="cmd", required=False)
    sub.add_parser("health", help="Print health JSON; exit 0 if ok else 1")
    sub.add_parser("overrides", help="Print Unbound host overrides as JSON")
    p.add_argument("--smoke", action="store_true",
                   help="Run smoke check (health + first 5 overrides)")
    args = p.parse_args(argv)

    if args.smoke:
        return _smoke()
    if args.cmd == "health":
        h = opnsense_health()
        print(json.dumps(h, indent=2))
        return 0 if h["ok"] else 1
    if args.cmd == "overrides":
        try:
            rows = opnsense_get_unbound_overrides()
        except OPNsenseClientError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(rows, indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
