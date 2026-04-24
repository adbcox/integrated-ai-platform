from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class MediaDomain:
    """Media Domain: Manages *Arr stack (Sonarr/Radarr/Prowlarr) automation."""

    def __init__(self):
        config = self._load_config()
        self.config = config
        self.enabled = config.get("enabled", False)
        self.sonarr_url = config.get("parameters", {}).get(
            "sonarr_url", "http://192.168.10.114:8989"
        )
        self.radarr_url = config.get("parameters", {}).get(
            "radarr_url", "http://192.168.10.114:7878"
        )
        self.prowlarr_url = config.get("parameters", {}).get(
            "prowlarr_url", "http://192.168.10.114:9696"
        )

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """Load MediaDomain config from config/domains.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "domains.yaml"
        if not config_path.exists():
            return {"enabled": False, "parameters": {}}

        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            return data.get("MediaDomain", {"enabled": False, "parameters": {}})

    def health_check(self) -> Dict[str, bool]:
        """Check health of all *Arr services."""
        from connectors.arr_stack import ArrStackConnector

        # API keys can be wired from config or environment later; keep this read-only.
        sonarr = ArrStackConnector("sonarr", self.sonarr_url)
        radarr = ArrStackConnector("radarr", self.radarr_url)
        prowlarr = ArrStackConnector("prowlarr", self.prowlarr_url)

        return {
            "sonarr": sonarr.health_check(),
            "radarr": radarr.health_check(),
            "prowlarr": prowlarr.health_check(),
        }
