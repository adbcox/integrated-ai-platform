"""ISP / Google Fiber connection monitor.

Tracks latency, packet loss, and periodically logs results.
Does NOT require speedtest-cli (avoids 30-second blocking tests on the hot path).
A background thread runs ping sweeps; the dashboard reads from the shared cache.

Usage:
    from domains.isp_monitor import ISPMonitor
    monitor = ISPMonitor()
    monitor.start()
    status = monitor.status()
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


# Targets to ping for connectivity / latency checks
_TARGETS = [
    {"name": "google_dns",   "host": "8.8.8.8",       "type": "dns"},
    {"name": "cloudflare",   "host": "1.1.1.1",        "type": "dns"},
    {"name": "gateway",      "host": "192.168.10.1",   "type": "local"},
    {"name": "google_fiber", "host": "74.125.29.1",    "type": "isp"},
]

_HISTORY_FILE = Path(__file__).parent.parent / "artifacts" / "isp_monitor.jsonl"


def _ping_once(host: str, count: int = 4) -> dict:
    """Ping host, return {rtt_ms, loss_pct, reachable}."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2000", "-q", host],
            capture_output=True, text=True, timeout=15,
        )
        out = result.stdout
        # "4 packets transmitted, 4 received, 0% packet loss"
        loss_pct = 100.0
        rtt_avg = None
        for line in out.splitlines():
            if "packet loss" in line:
                parts = line.split(",")
                for p in parts:
                    if "packet loss" in p:
                        loss_pct = float(p.strip().split("%")[0])
            if line.startswith("round-trip") or line.startswith("rtt"):
                # "round-trip min/avg/max/stddev = 1.2/2.3/3.4/0.4 ms"
                stats = line.split("=")[-1].strip().split("/")
                if len(stats) >= 2:
                    rtt_avg = float(stats[1])
        return {
            "rtt_ms": rtt_avg,
            "loss_pct": loss_pct,
            "reachable": loss_pct < 100,
        }
    except Exception as exc:
        return {"rtt_ms": None, "loss_pct": 100.0, "reachable": False,
                "error": str(exc)}


def _run_check(targets: list[dict]) -> dict:
    results: dict[str, Any] = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "targets": {},
    }
    for t in targets:
        results["targets"][t["name"]] = {
            **_ping_once(t["host"]),
            "host": t["host"],
            "type": t["type"],
        }
    # Overall internet: google_dns or cloudflare reachable
    inet = results["targets"]
    results["internet_up"] = (
        inet.get("google_dns", {}).get("reachable", False)
        or inet.get("cloudflare", {}).get("reachable", False)
    )
    results["gateway_up"] = inet.get("gateway", {}).get("reachable", False)
    gw_rtt = inet.get("gateway", {}).get("rtt_ms")
    ext_rtt = inet.get("google_dns", {}).get("rtt_ms")
    results["gateway_rtt_ms"] = gw_rtt
    results["external_rtt_ms"] = ext_rtt
    return results


class ISPMonitor:
    """Background monitor — runs ping checks every `interval` seconds."""

    def __init__(self, interval: int = 60, targets: list[dict] | None = None):
        self._interval = interval
        self._targets = targets or _TARGETS
        self._lock = threading.Lock()
        self._latest: dict | None = None
        self._history: list[dict] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            result = _run_check(self._targets)
            with self._lock:
                self._latest = result
                self._history.append(result)
                if len(self._history) > 1440:  # 24h at 1/min
                    self._history.pop(0)
            self._persist(result)
            time.sleep(self._interval)

    def _persist(self, record: dict) -> None:
        try:
            _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_HISTORY_FILE, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def status(self) -> dict:
        with self._lock:
            return dict(self._latest) if self._latest else {"status": "initializing"}

    def recent_history(self, n: int = 60) -> list[dict]:
        with self._lock:
            return list(self._history[-n:])

    def run_once(self) -> dict:
        """Blocking single check (for CLI/tests)."""
        result = _run_check(self._targets)
        with self._lock:
            self._latest = result
        return result


# Module-level singleton started by server.py
_monitor: ISPMonitor | None = None


def get_monitor() -> ISPMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ISPMonitor(
            interval=int(os.environ.get("ISP_MONITOR_INTERVAL", "60"))
        )
    return _monitor
