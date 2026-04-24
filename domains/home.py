from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any
import yaml


class HomeDomain:
    """Home Domain: Integrates Home Assistant for device control."""

    def __init__(self):
        config = self._load_config()
        self.config = config
        self.enabled = config.get("enabled", False)
        self.ha_url = config.get("parameters", {}).get("ha_url", "http://homeassistant.local:8123")
        self.ha_token = config.get("parameters", {}).get("ha_token", "")

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "domains.yaml"
        if not config_path.exists():
            return {"enabled": False, "parameters": {}}
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            return data.get("HomeDomain", {"enabled": False})

    def health_check(self) -> bool:
        """Check HA connectivity."""
        # Stub - will implement via HAConnector
        return False
