"""New domain scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class ExampleDomain:
    """Domain scaffold for config-driven orchestration."""

    def __init__(self):
        self.config = self._load_config()
        self.enabled = self.config.get("enabled", False)

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        config_path = Path(__file__).resolve().parent.parent / "config" / "domains.yaml"
        if not config_path.exists():
            return {"enabled": False, "parameters": {}}
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            return data.get("ExampleDomain", {"enabled": False, "parameters": {}})
