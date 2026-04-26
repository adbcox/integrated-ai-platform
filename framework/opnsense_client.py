"""OPNsense REST API client.

Usage:
    from framework.opnsense_client import OPNsenseClient
    api = OPNsenseClient.from_env()
    print(api.get_system_info())

Env vars:
    OPNSENSE_HOST        IP/hostname of firewall (e.g. 192.168.10.1)
    OPNSENSE_API_KEY     API key from System → Access → Users → API
    OPNSENSE_API_SECRET  Paired API secret
    OPNSENSE_VERIFY_SSL  "1" to verify cert (default: 0, self-signed is normal)
"""
from __future__ import annotations

import os
import urllib.request
import urllib.error
import base64
import json
import ssl
from typing import Any


class OPNsenseClient:

    def __init__(self, host: str, api_key: str, api_secret: str,
                 verify_ssl: bool = False, timeout: int = 10):
        self.base_url = f"https://{host}/api"
        self._auth = base64.b64encode(
            f"{api_key}:{api_secret}".encode()
        ).decode()
        self._timeout = timeout
        self._ctx = ssl.create_default_context()
        if not verify_ssl:
            self._ctx.check_hostname = False
            self._ctx.verify_mode = ssl.CERT_NONE

    @classmethod
    def from_env(cls) -> "OPNsenseClient":
        host = os.environ.get("OPNSENSE_HOST", "192.168.10.1")
        key = os.environ.get("OPNSENSE_API_KEY", "")
        secret = os.environ.get("OPNSENSE_API_SECRET", "")
        verify = os.environ.get("OPNSENSE_VERIFY_SSL", "0") == "1"
        return cls(host, key, secret, verify_ssl=verify)

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {self._auth}",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=self._timeout,
                                    context=self._ctx) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, body: dict | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }, method="POST")
        with urllib.request.urlopen(req, timeout=self._timeout,
                                    context=self._ctx) as resp:
            return json.loads(resp.read())

    # ── System ────────────────────────────────────────────────────────────────

    def get_system_info(self) -> dict:
        """Firmware version, uptime, CPU, memory."""
        return self._get("/core/system/status")

    def get_firmware_version(self) -> dict:
        return self._get("/core/firmware/status")

    # ── Network interfaces ────────────────────────────────────────────────────

    def get_interfaces(self) -> dict:
        """All interface names keyed by internal name."""
        return self._get("/diagnostics/interface/getInterfaceNames")

    def get_interface_stats(self) -> dict:
        """Per-interface rx/tx bytes, errors, drops."""
        return self._get("/diagnostics/interface/getInterfaceStatistics")

    def get_traffic(self) -> dict:
        """Real-time traffic rates per interface."""
        return self._get("/diagnostics/traffic/interface")

    # ── Gateways & routing ────────────────────────────────────────────────────

    def get_gateway_status(self) -> list[dict]:
        """Gateway list with status, RTT, loss %."""
        data = self._get("/routes/gateway/status")
        return data.get("items", data) if isinstance(data, dict) else data

    def get_arp_table(self) -> list[dict]:
        """ARP table — IP → MAC mappings."""
        data = self._get("/diagnostics/interface/getArp")
        return data.get("rows", []) if isinstance(data, dict) else data

    # ── DHCP leases ───────────────────────────────────────────────────────────

    def get_dhcp_leases(self) -> list[dict]:
        """Active DHCP leases with hostname, IP, MAC, expiry."""
        data = self._get("/dhcpv4/leases/searchLease")
        return data.get("rows", []) if isinstance(data, dict) else data

    # ── Services ──────────────────────────────────────────────────────────────

    def get_service_status(self) -> list[dict]:
        data = self._get("/core/service/search")
        return data.get("rows", []) if isinstance(data, dict) else data

    # ── Convenience summary ───────────────────────────────────────────────────

    def summary(self) -> dict:
        """Single-call summary for the dashboard — tolerates individual failures."""
        result: dict[str, Any] = {"host": self.base_url}
        for key, fn in [
            ("system", self.get_system_info),
            ("gateways", self.get_gateway_status),
            ("traffic", self.get_traffic),
            ("arp", self.get_arp_table),
        ]:
            try:
                result[key] = fn()
            except Exception as exc:
                result[key] = {"error": str(exc)}
        return result
