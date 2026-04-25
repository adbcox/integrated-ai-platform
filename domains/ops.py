"""Operations domain — system operational tasks, health checks, maintenance."""
from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

log = logging.getLogger(__name__)


class OpsManager:
    """Manages operational health checks and system status."""

    def __init__(self) -> None:
        self._checks: List[Dict] = []
        self.last_health: Dict = {}

    def register_health_check(self, name: str, check_fn: Callable) -> None:
        self._checks.append({"name": name, "function": check_fn})

    def run_health_checks(self) -> Dict:
        results: Dict = {}
        for check in self._checks:
            try:
                results[check["name"]] = check["function"]()
            except Exception as exc:
                log.error("Health check %s failed: %s", check["name"], exc)
                results[check["name"]] = {"status": "error", "message": str(exc)}
        self.last_health = results
        return results

    def get_system_status(self) -> Dict:
        healthy = all(
            r.get("status") == "ok" for r in self.last_health.values()
        ) if self.last_health else True
        return {"healthy": healthy, "checks": self.last_health}


_ops_manager: Optional[OpsManager] = None


def get_ops_manager() -> OpsManager:
    global _ops_manager
    if _ops_manager is None:
        _ops_manager = OpsManager()
    return _ops_manager
