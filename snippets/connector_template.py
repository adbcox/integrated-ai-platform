"""New connector scaffold."""

from __future__ import annotations

from typing import Any, Dict

from connectors.base import BaseConnector


class ExampleConnector(BaseConnector):
    """Connector scaffold for a read-only service integration."""

    def __init__(self, base_url: str, api_key: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def health_check(self) -> bool:
        """Return whether the service is reachable."""
        return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch an action and return a structured result."""
        return {"success": False, "error": "Not implemented"}
