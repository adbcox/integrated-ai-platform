"""Per-task-class routing configuration with threshold overrides.

Allows evidence-driven override of the degraded failure rate threshold
used by route_task(). Default behavior is unchanged when routing_config=None.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

_DEFAULT_ARTIFACT_PATH = Path("artifacts") / "routing_config" / "routing_config.json"
_GLOBAL_DEFAULT_THRESHOLD = 0.6


@dataclass
class TaskRoutingOverride:
    task_class: str
    degraded_failure_rate_threshold: float


@dataclass
class RoutingConfig:
    overrides: list[TaskRoutingOverride] = field(default_factory=list)
    global_threshold: float = _GLOBAL_DEFAULT_THRESHOLD

    def threshold_for(self, task_class: str) -> float:
        """Return threshold for task_class; falls back to global_threshold."""
        for override in self.overrides:
            if override.task_class == task_class:
                return override.degraded_failure_rate_threshold
        return self.global_threshold

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "global_threshold": self.global_threshold,
            "overrides": [asdict(o) for o in self.overrides],
        }


DEFAULT_ROUTING_CONFIG = RoutingConfig()


def load_routing_config(path: Optional[Path] = None) -> RoutingConfig:
    """Load RoutingConfig from JSON artifact, or return DEFAULT_ROUTING_CONFIG."""
    p = Path(path) if path else _DEFAULT_ARTIFACT_PATH
    if not p.exists():
        return DEFAULT_ROUTING_CONFIG
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        overrides = [
            TaskRoutingOverride(**o) for o in data.get("overrides", [])
        ]
        return RoutingConfig(
            overrides=overrides,
            global_threshold=data.get("global_threshold", _GLOBAL_DEFAULT_THRESHOLD),
        )
    except Exception:
        return DEFAULT_ROUTING_CONFIG


def save_routing_config(
    config: RoutingConfig,
    *,
    path: Optional[Path] = None,
    dry_run: bool = False,
) -> Optional[str]:
    """Write routing config to JSON. Returns path or None on dry_run."""
    if dry_run:
        return None
    p = Path(path) if path else _DEFAULT_ARTIFACT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


__all__ = [
    "TaskRoutingOverride",
    "RoutingConfig",
    "DEFAULT_ROUTING_CONFIG",
    "load_routing_config",
    "save_routing_config",
]
