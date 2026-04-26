"""QNAP NAS API client (CGI + QTS REST).

Usage:
    from framework.qnap_client import QNAPClient
    api = QNAPClient.from_env()
    print(api.summary())

Env vars:
    QNAP_HOST      IP/hostname (e.g. 192.168.10.200)
    QNAP_USER      Admin username
    QNAP_PASSWORD  Admin password
    QNAP_PORT      HTTP port (default 8080; use 443 + QNAP_HTTPS=1 for HTTPS)
    QNAP_HTTPS     "1" to use HTTPS
"""
from __future__ import annotations

import hashlib
import os
import urllib.parse
import urllib.request
import urllib.error
import ssl
import json
import xml.etree.ElementTree as ET
from typing import Any


def _md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


class QNAPClient:

    def __init__(self, host: str, username: str, password: str,
                 port: int = 8080, https: bool = False):
        scheme = "https" if https else "http"
        self.base_url = f"{scheme}://{host}:{port}"
        self._username = username
        self._password = password
        self._sid: str | None = None
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE

    @classmethod
    def from_env(cls) -> "QNAPClient":
        return cls(
            host=os.environ.get("QNAP_HOST", "192.168.10.200"),
            username=os.environ.get("QNAP_USER", "admin"),
            password=os.environ.get("QNAP_PASSWORD", ""),
            port=int(os.environ.get("QNAP_PORT", "8080")),
            https=os.environ.get("QNAP_HTTPS", "0") == "1",
        )

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _cgi(self, cgi: str, params: dict) -> str:
        url = f"{self.base_url}/cgi-bin/{cgi}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10, context=self._ctx) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _login(self) -> str:
        pwd_hash = _md5(self._password)
        text = self._cgi("authLogin.cgi", {
            "user": self._username,
            "pwd": pwd_hash,
        })
        root = ET.fromstring(text)
        sid_el = root.find(".//authSid")
        if sid_el is None or not sid_el.text:
            raise RuntimeError(f"QNAP login failed: {text[:200]}")
        return sid_el.text

    def _sid_or_login(self) -> str:
        if not self._sid:
            self._sid = self._login()
        return self._sid

    def _xml(self, cgi: str, params: dict) -> ET.Element:
        params["sid"] = self._sid_or_login()
        text = self._cgi(cgi, params)
        return ET.fromstring(text)

    @staticmethod
    def _xml_to_dict(el: ET.Element) -> dict:
        """Shallow XML element to dict."""
        return {child.tag: (child.text or "").strip() for child in el}

    # ── System stats ──────────────────────────────────────────────────────────

    def get_system_stats(self) -> dict:
        """CPU %, memory %, uptime, temperature."""
        root = self._xml("management/manaRequest.cgi", {
            "subfunc": "sysinfo",
            "hd": "no",
            "multi_lan": "yes",
        })
        return self._xml_to_dict(root)

    def get_volume_info(self) -> list[dict]:
        """Storage volumes with used/free/total bytes."""
        root = self._xml("disk/disk_manage.cgi", {"func": "vol_info"})
        return [self._xml_to_dict(v) for v in root.findall(".//volume")]

    def get_disk_health(self) -> list[dict]:
        """S.M.A.R.T. status per physical drive."""
        root = self._xml("disk/disk_manage.cgi", {"func": "disk_info"})
        return [self._xml_to_dict(d) for d in root.findall(".//disk")]

    def get_network_stats(self) -> list[dict]:
        """NIC stats: rx/tx bytes, errors."""
        root = self._xml("management/manaRequest.cgi", {
            "subfunc": "sysinfo",
            "hd": "no",
        })
        return [self._xml_to_dict(n) for n in root.findall(".//nic")]

    def get_running_processes(self) -> list[dict]:
        """Top processes by CPU."""
        root = self._xml("management/manaRequest.cgi", {
            "subfunc": "process_status",
        })
        return [self._xml_to_dict(p) for p in root.findall(".//process")]

    # ── File station (optional) ───────────────────────────────────────────────

    def list_shares(self) -> list[dict]:
        """Shared folders."""
        root = self._xml("filemanager/utilRequest.cgi", {
            "func": "get_tree",
            "node": "share_root",
            "is_iso": "0",
        })
        return [self._xml_to_dict(f) for f in root.findall(".//file")]

    # ── Convenience summary ───────────────────────────────────────────────────

    def summary(self) -> dict:
        """Dashboard summary — tolerates individual failures."""
        result: dict[str, Any] = {"host": self.base_url}
        for key, fn in [
            ("system", self.get_system_stats),
            ("volumes", self.get_volume_info),
            ("disks", self.get_disk_health),
        ]:
            try:
                result[key] = fn()
            except Exception as exc:
                result[key] = {"error": str(exc)}
        return result
