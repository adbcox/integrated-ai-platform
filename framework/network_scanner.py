"""Network topology scanner.

Uses nmap (if available) or ping sweep to discover live hosts, then enriches
with ARP/DHCP data.  Results are cached and served to the Network tab.

Usage:
    from framework.network_scanner import NetworkScanner
    ns = NetworkScanner("192.168.10.0/24")
    topology = ns.scan()
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any

# Known static devices — merged into scan results
_KNOWN_DEVICES: list[dict] = [
    {"ip": "192.168.10.1",   "name": "OPNsense",      "role": "firewall",   "icon": "🔥", "vendor": "OPNsense"},
    {"ip": "192.168.10.2",   "name": "Brocade Switch","role": "switch",     "icon": "🔀", "vendor": "Brocade"},
    {"ip": "192.168.10.3",   "name": "TP-Link Deco",  "role": "mesh_ap",    "icon": "📡", "vendor": "TP-Link"},
    {"ip": "192.168.10.145", "name": "Mac Mini",       "role": "worker",     "icon": "💻", "vendor": "Apple"},
    {"ip": "192.168.10.200", "name": "QNAP NAS",       "role": "storage",    "icon": "💾", "vendor": "QNAP"},
    {"ip": "192.168.10.210", "name": "Mac Studio",     "role": "gpu_worker", "icon": "🖥️",  "vendor": "Apple"},
]

_KNOWN_BY_IP = {d["ip"]: d for d in _KNOWN_DEVICES}


@dataclass
class Host:
    ip: str
    name: str = ""
    mac: str = ""
    vendor: str = ""
    role: str = "unknown"
    icon: str = "❓"
    ports: list[int] = field(default_factory=list)
    alive: bool = True
    last_seen: float = field(default_factory=time.time)
    latency_ms: float | None = None


def _nmap_available() -> bool:
    return subprocess.run(
        ["which", "nmap"], capture_output=True
    ).returncode == 0


def _ping(ip: str, timeout: float = 0.5) -> float | None:
    """Return RTT in ms or None if unreachable."""
    try:
        t0 = time.monotonic()
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "500", "-t", "1", ip],
            capture_output=True, timeout=2,
        )
        if result.returncode == 0:
            return (time.monotonic() - t0) * 1000
    except Exception:
        pass
    return None


def _nmap_scan(subnet: str) -> list[Host]:
    """Fast nmap host discovery with OS/vendor detection."""
    try:
        result = subprocess.run(
            ["nmap", "-sn", "-T4", "--host-timeout", "3s",
             "--oX", "-", subnet],
            capture_output=True, text=True, timeout=60,
        )
        hosts = []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(result.stdout)
        for host_el in root.findall(".//host"):
            status = host_el.find(".//status")
            if status is None or status.get("state") != "up":
                continue
            addr_el = host_el.find(".//address[@addrtype='ipv4']")
            mac_el  = host_el.find(".//address[@addrtype='mac']")
            hn_el   = host_el.find(".//hostname[@type='PTR']")

            ip     = addr_el.get("addr", "") if addr_el is not None else ""
            mac    = mac_el.get("addr", "") if mac_el is not None else ""
            vendor = mac_el.get("vendor", "") if mac_el is not None else ""
            name   = hn_el.get("name", "") if hn_el is not None else ""

            if not ip:
                continue

            known = _KNOWN_BY_IP.get(ip, {})
            hosts.append(Host(
                ip=ip,
                name=name or known.get("name", ""),
                mac=mac,
                vendor=vendor or known.get("vendor", ""),
                role=known.get("role", "unknown"),
                icon=known.get("icon", "❓"),
                alive=True,
            ))
        return hosts
    except Exception as exc:
        return []


def _ping_sweep(subnet: str, workers: int = 30) -> list[Host]:
    """Parallel ping sweep when nmap isn't available."""
    match = re.match(r"(\d+\.\d+\.\d+)\.\d+/24", subnet)
    if not match:
        return []
    prefix = match.group(1)
    ips = [f"{prefix}.{i}" for i in range(1, 255)]

    results: list[Host] = []
    lock = threading.Lock()

    def check(ip: str) -> None:
        rtt = _ping(ip)
        if rtt is not None:
            known = _KNOWN_BY_IP.get(ip, {})
            h = Host(
                ip=ip,
                name=known.get("name", ""),
                vendor=known.get("vendor", ""),
                role=known.get("role", "unknown"),
                icon=known.get("icon", "❓"),
                alive=True,
                latency_ms=round(rtt, 1),
            )
            try:
                h.name = h.name or socket.gethostbyaddr(ip)[0]
            except Exception:
                pass
            with lock:
                results.append(h)

    threads = []
    for ip in ips:
        while len(threads) >= workers:
            threads = [t for t in threads if t.is_alive()]
            time.sleep(0.01)
        t = threading.Thread(target=check, args=(ip,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=5)

    return sorted(results, key=lambda h: [int(o) for o in h.ip.split(".")])


class NetworkScanner:
    """Scan and cache network topology."""

    def __init__(self, subnet: str | None = None, cache_ttl: int = 300):
        self.subnet = subnet or os.environ.get(
            "NETWORK_SUBNET", "192.168.10.0/24"
        )
        self._ttl = cache_ttl
        self._lock = threading.Lock()
        self._hosts: list[Host] = []
        self._scanned_at: float = 0.0

    def scan(self, force: bool = False) -> dict:
        with self._lock:
            if not force and time.time() - self._scanned_at < self._ttl:
                return self._to_topology()

        if _nmap_available():
            hosts = _nmap_scan(self.subnet)
        else:
            hosts = _ping_sweep(self.subnet)

        # Merge known-but-not-found devices as offline
        found_ips = {h.ip for h in hosts}
        for known in _KNOWN_DEVICES:
            if known["ip"] not in found_ips:
                hosts.append(Host(
                    ip=known["ip"],
                    name=known["name"],
                    vendor=known["vendor"],
                    role=known["role"],
                    icon=known["icon"],
                    alive=False,
                ))

        with self._lock:
            self._hosts = hosts
            self._scanned_at = time.time()
            return self._to_topology()

    def _to_topology(self) -> dict:
        nodes = []
        edges = []
        gateway_ip = "192.168.10.1"

        for h in self._hosts:
            nodes.append({
                "id": h.ip,
                "label": f"{h.icon} {h.name or h.ip}",
                "ip": h.ip,
                "name": h.name,
                "role": h.role,
                "vendor": h.vendor,
                "alive": h.alive,
                "latency_ms": h.latency_ms,
                "color": "#00d4ff" if h.alive else "#444",
                "group": h.role,
            })
            # Connect everything to gateway except the gateway itself
            if h.ip != gateway_ip:
                edges.append({
                    "from": gateway_ip,
                    "to": h.ip,
                    "color": "#00d4ff" if h.alive else "#333",
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "subnet": self.subnet,
            "scanned_at": self._scanned_at,
            "total": len(self._hosts),
            "alive": sum(1 for h in self._hosts if h.alive),
        }

    def quick_status(self) -> dict:
        """Return cached topology without re-scanning."""
        with self._lock:
            return self._to_topology()


# Module-level singleton
_scanner: NetworkScanner | None = None


def get_scanner() -> NetworkScanner:
    global _scanner
    if _scanner is None:
        _scanner = NetworkScanner()
    return _scanner
