from __future__ import annotations

from typing import Any, Dict

from .base import BaseConnector


class ArrStackConnector(BaseConnector):
    """Connector for *Arr stack (Sonarr/Radarr/Prowlarr)."""

    def __init__(self, service_name: str, base_url: str, api_key: str = ""):
        super().__init__()
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def health_check(self) -> bool:
        """Check if service is reachable."""
        # Stub - will implement with requests
        return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on *Arr service."""
        # Stub - actions: get_queue, get_calendar, add_series, etc.
        return {"success": False, "error": "Not implemented"}
