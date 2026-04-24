from __future__ import annotations

from .base import BaseConnector
from typing import Dict, Any


class HomeAssistantConnector(BaseConnector):
    """Connector for Home Assistant REST API."""

    def __init__(self, base_url: str, token: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.token = token

    def health_check(self) -> bool:
        """Check if HA is reachable."""
        # Stub - will implement with requests
        return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HA action."""
        # Stub - actions: get_state, call_service, etc.
        return {"success": False, "error": "Not implemented"}
