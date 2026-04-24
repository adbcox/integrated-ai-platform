from __future__ import annotations

import requests
import logging
from typing import List, Dict, Any

from .base import BaseConnector


class ArrStackConnector(BaseConnector):
    """Connector for *Arr stack (Sonarr/Radarr/Prowlarr)."""

    def __init__(self, service_name: str, base_url: str, api_key: str = ""):
        super().__init__()
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-Api-Key": api_key})

    def health_check(self) -> bool:
        """Check if service is reachable."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/system/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error checking health: {e}")
            return False

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get current download queue."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/queue", timeout=10)
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception as e:
            logging.error(f"Error getting queue: {e}")
            return []

    def get_calendar(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming releases/episodes."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v3/calendar",
                params={"start": "today", "end": f"{days}d"},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error getting calendar: {e}")
            return []

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on service."""
        actions = {
            "health_check": lambda: {"healthy": self.health_check()},
            "get_queue": lambda: {"queue": self.get_queue()},
            "get_calendar": lambda: {"calendar": self.get_calendar(params.get("days", 7))},
        }

        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            result = handler()
            return {"success": True, **result}
        except Exception as e:
            logging.error(f"Error executing action '{action}': {e}")
            return {"success": False, "error": str(e)}
