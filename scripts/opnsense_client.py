#!/usr/bin/env python3
"""D-17-09 — OPNsense API client (Dnsmasq host records + health).

Reads `secret/opnsense/api` (fields: api_key, api_secret, host) via the
`opnsense-api-reader` Vault AppRole and exposes two functions used by
drift detection (D-16-06 + D-17-09):

    opnsense_get_host_records() -> list[dict]
        Each row: {"hostname": str, "domain": str, "fqdn": str,
                   "ip": str, "rr": str, "enabled": bool, "uuid": str}
    opnsense_health() -> dict
        {"ok": bool, "vault_ok": bool, "api_ok": bool,
         "record_count": int|None, "error": str|None}

Note: queries Dnsmasq, NOT Unbound. Dnsmasq is the DNS authority on
this platform — see docs/architecture-facts/opnsense-dns-authority.md
and KI-009. The deprecated alias opnsense_get_unbound_overrides() is
retained for one cycle.

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
            "Run T1 of D-17-09 to provision."
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


def opnsense_get_host_records() -> list[dict]:
    """Returns Dnsmasq host records as a list of normalized dicts.

    Endpoint: /api/dnsmasq/settings/get
    Source map shape: payload[".dnsmasq.hosts"] is a {uuid: row} dict
    (not a list). Each row's `ip` field is itself a dict whose key is
    the IP and whose value carries `selected`/`value`. We pull out the
    selected IP.

    Dnsmasq is the DNS authority on this platform; Unbound's host
    override module is unused. See
    docs/architecture-facts/opnsense-dns-authority.md and KI-009.

    Returned shape (subset, normalized — same as the prior Unbound
    helper so consumers don't need to change):
        {"hostname": "plane", "domain": "internal",
         "fqdn": "plane.internal", "ip": "192.168.10.145",
         "rr": "A", "enabled": True, "uuid": "..."}
    """
    key, secret, host = _load_credentials()
    payload = _opnsense_get(key, secret, host, "/api/dnsmasq/settings/get")
    hosts_map = ((payload.get("dnsmasq") or {}).get("hosts") or {})
    out: list[dict] = []
    for uuid, r in hosts_map.items():
        if not isinstance(r, dict):
            continue
        hostname = (r.get("host") or "").strip()
        if not hostname:
            continue
        domain = (r.get("domain") or "").strip()
        # Strip any accidental trailing dots; treat `host=foo.internal,domain=`
        # as a bare-FQDN entry for downstream matching.
        if hostname.endswith("."):
            hostname = hostname.rstrip(".")
        ip = ""
        ip_field = r.get("ip")
        if isinstance(ip_field, dict):
            for ip_key, meta in ip_field.items():
                if isinstance(meta, dict) and str(meta.get("selected") or "0") == "1":
                    ip = (meta.get("value") or ip_key or "").strip()
                    break
            if not ip:
                # Fallback: first key (some OPNsense versions emit a flat dict)
                first = next(iter(ip_field), None)
                if first:
                    ip = first.strip()
        elif isinstance(ip_field, str):
            ip = ip_field.strip()
        fqdn = f"{hostname}.{domain}" if domain else hostname
        out.append({
            "hostname": hostname,
            "domain": domain,
            "fqdn": fqdn,
            "ip": ip,
            "rr": "A",  # Dnsmasq host entries are A records
            "enabled": str(r.get("enabled") or "1") == "1",
            "uuid": uuid,
        })
    return out


def opnsense_get_unbound_overrides(*args, **kwargs):
    """Deprecated alias. Renamed because Dnsmasq, not Unbound, is the
    authority on this platform. See
    docs/architecture-facts/opnsense-dns-authority.md."""
    import warnings
    warnings.warn(
        "opnsense_get_unbound_overrides is deprecated; "
        "use opnsense_get_host_records (queries Dnsmasq, the actual "
        "authority on this platform). Will be removed in cleanup pass.",
        DeprecationWarning, stacklevel=2,
    )
    return opnsense_get_host_records(*args, **kwargs)


def opnsense_health() -> dict:
    """Returns connectivity + auth status without raising.
    Suitable for status-file pattern (D-16-06).

    Probes the Dnsmasq settings endpoint (the authority on this
    platform; see docs/architecture-facts/opnsense-dns-authority.md).
    `override_count` is retained as a stable alias for `record_count`
    so downstream readers of the status file don't break in this
    one-cycle deprecation window."""
    result = {
        "ok": False, "vault_ok": False, "api_ok": False,
        "record_count": None, "override_count": None, "error": None,
    }
    try:
        key, secret, host = _load_credentials()
        result["vault_ok"] = True
    except OPNsenseClientError as exc:
        result["error"] = f"vault: {exc}"
        return result
    try:
        payload = _opnsense_get(key, secret, host, "/api/dnsmasq/settings/get")
        hosts_map = ((payload.get("dnsmasq") or {}).get("hosts") or {})
        count = sum(
            1 for r in hosts_map.values()
            if isinstance(r, dict) and (r.get("host") or "").strip()
        )
        result["api_ok"] = True
        result["record_count"] = count
        result["override_count"] = count  # deprecated alias (one cycle)
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
    print("== opnsense_get_host_records() (first 5) ==")
    rows = opnsense_get_host_records()
    print(f"Total: {len(rows)}")
    for r in rows[:5]:
        print(f"  {r['fqdn']:40s} -> {r['ip']:18s} {r['rr']:5s} en={r['enabled']}")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="opnsense_client",
        description="OPNsense API client — Dnsmasq host records + health.",
    )
    sub = p.add_subparsers(dest="cmd", required=False)
    sub.add_parser("health", help="Print health JSON; exit 0 if ok else 1")
    sub.add_parser("records", help="Print Dnsmasq host records as JSON")
    sub.add_parser("overrides",
                   help="(deprecated alias for `records`) prints Dnsmasq host records as JSON")
    p.add_argument("--smoke", action="store_true",
                   help="Run smoke check (health + first 5 records)")
    args = p.parse_args(argv)

    if args.smoke:
        return _smoke()
    if args.cmd == "health":
        h = opnsense_health()
        print(json.dumps(h, indent=2))
        return 0 if h["ok"] else 1
    if args.cmd in ("records", "overrides"):
        try:
            rows = opnsense_get_host_records()
        except OPNsenseClientError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(rows, indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
