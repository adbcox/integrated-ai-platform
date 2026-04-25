"""Docker container monitoring — status, resource usage, security posture."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# Lazy import — docker SDK optional
_docker = None


def _get_docker_client():
    global _docker
    if _docker is None:
        try:
            import docker as _sdk
            import os
            # Try default first, then Colima socket
            sockets = [
                None,  # from_env() default
                os.path.expanduser("~/.colima/default/docker.sock"),
                "/var/run/docker.sock",
            ]
            for sock in sockets:
                try:
                    if sock:
                        _docker = _sdk.DockerClient(base_url=f"unix://{sock}")
                    else:
                        _docker = _sdk.from_env()
                    _docker.ping()
                    break
                except Exception:
                    _docker = None
        except Exception:
            pass
    return _docker


def _cpu_percent(stats: Dict) -> float:
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        sys_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        ncpu = stats["cpu_stats"].get("online_cpus", 1)
        if sys_delta > 0:
            return round((cpu_delta / sys_delta) * ncpu * 100.0, 2)
    except Exception:
        pass
    return 0.0


def _uptime(container) -> str:
    if container.status != "running":
        return "stopped"
    try:
        started = container.attrs["State"]["StartedAt"].replace("Z", "+00:00")
        start_dt = datetime.fromisoformat(started)
        delta = datetime.now(timezone.utc) - start_dt
        days, rem = divmod(int(delta.total_seconds()), 86400)
        hrs, rem = divmod(rem, 3600)
        mins = rem // 60
        if days:
            return f"{days}d {hrs}h"
        if hrs:
            return f"{hrs}h {mins}m"
        return f"{mins}m"
    except Exception:
        return "unknown"


def _ports(container) -> str:
    try:
        ports = container.attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
        exposed = sorted(
            ext[0]["HostPort"]
            for ext in ports.values()
            if ext
        )
        return ", ".join(f":{p}" for p in exposed) if exposed else "internal"
    except Exception:
        return "—"


class DockerMonitor:
    """Snapshots all Docker containers with resource stats and security posture."""

    # Cache for 8 s — stats() blocks for ~1 s per running container
    _cache: Optional[Dict] = None
    _cache_until: float = 0.0
    _lock = threading.Lock()

    def get_all_containers(self) -> List[Dict]:
        client = _get_docker_client()
        if not client:
            return []

        results: List[Dict] = []
        for c in client.containers.list(all=True):
            entry: Dict = {
                "id":            c.id[:12],
                "name":          c.name,
                "image":         (c.image.tags[0] if c.image.tags else c.image.short_id),
                "status":        c.status,
                "health":        (c.attrs.get("State", {}).get("Health", {}) or {}).get("Status", "—"),
                "cpu_percent":   0.0,
                "memory_mb":     0.0,
                "memory_limit_mb": 0.0,
                "uptime":        _uptime(c),
                "restart_count": c.attrs.get("RestartCount", 0),
                "ports":         _ports(c),
            }
            if c.status == "running":
                try:
                    stats = c.stats(stream=False)
                    entry["cpu_percent"]      = _cpu_percent(stats)
                    mem                       = stats.get("memory_stats", {})
                    entry["memory_mb"]        = round(mem.get("usage", 0) / 1048576, 1)
                    entry["memory_limit_mb"]  = round(mem.get("limit", 0) / 1048576, 1)
                except Exception:
                    pass
            results.append(entry)

        results.sort(key=lambda x: (x["status"] != "running", x["name"]))
        return results

    def get_security_posture(self) -> Dict:
        client = _get_docker_client()
        if not client:
            return {"error": "Docker SDK unavailable", "score": 0, "issues": []}

        issues: List[str] = []
        containers = client.containers.list(all=True)

        privileged = [
            c.name for c in containers
            if c.attrs.get("HostConfig", {}).get("Privileged")
        ]
        if privileged:
            issues.append(f"{len(privileged)} privileged container(s): {', '.join(privileged)}")

        root_runners = [
            c.name for c in containers
            if c.status == "running"
            and c.attrs.get("Config", {}).get("User", "") in ("", "root", "0")
        ]
        if root_runners:
            issues.append(f"{len(root_runners)} container(s) running as root")

        no_healthcheck = [
            c.name for c in containers
            if c.status == "running"
            and not c.attrs.get("State", {}).get("Health")
        ]
        if no_healthcheck:
            issues.append(
                f"{len(no_healthcheck)} running container(s) without healthcheck"
            )

        score = max(0, 100 - len(issues) * 15)
        return {
            "score":                 score,
            "issues":                issues,
            "privileged_count":      len(privileged),
            "root_runner_count":     len(root_runners),
            "no_healthcheck_count":  len(no_healthcheck),
            "total_containers":      len(containers),
        }

    def get_snapshot(self) -> Dict:
        """Cached combined snapshot (containers + security), refreshes every 8 s."""
        with self._lock:
            now = time.monotonic()
            if self._cache and now < self._cache_until:
                return dict(self._cache)

        containers = self.get_all_containers()
        security   = self.get_security_posture()

        running = [c for c in containers if c["status"] == "running"]
        total_mem = sum(c["memory_mb"] for c in running)

        snap = {
            "containers":     containers,
            "security":       security,
            "summary": {
                "total":      len(containers),
                "running":    len(running),
                "stopped":    len(containers) - len(running),
                "total_mem_mb": round(total_mem, 1),
            },
        }
        with self._lock:
            self._cache       = snap
            self._cache_until = time.monotonic() + 8.0
        return snap


_monitor: Optional[DockerMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor() -> DockerMonitor:
    global _monitor
    if _monitor is None:
        with _monitor_lock:
            if _monitor is None:
                _monitor = DockerMonitor()
    return _monitor
