from __future__ import annotations

import os
import requests
import logging
from typing import Dict, Any, List

from .base import BaseConnector


class PlexConnector(BaseConnector):
    """Connector for Plex Media Server."""

    def __init__(self, base_url: str, token: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("PLEX_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-Plex-Token": self.token,
        })

    def health_check(self) -> bool:
        """Use /identity — public endpoint that returns 200 without auth."""
        try:
            response = self.session.get(f"{self.base_url}/identity", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logging.debug(f"Plex health check failed: {e}")
            return False

    def get_server_info(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            response.raise_for_status()
            data = response.json()
            media_container = data.get("MediaContainer", {})
            return {
                "friendly_name": media_container.get("friendlyName", ""),
                "version": media_container.get("version", ""),
                "platform": media_container.get("platform", ""),
            }
        except Exception:
            return {}

    def _get_xml(self, path: str, timeout: int = 10):
        """Fetch Plex XML and parse it. Returns element or raises."""
        import xml.etree.ElementTree as ET
        url = f"{self.base_url}{path}"
        r = requests.get(url, headers={"X-Plex-Token": self.token}, timeout=timeout)
        if r.status_code == 401:
            raise PermissionError("Plex token invalid or missing — set PLEX_TOKEN to account auth token (not machine ID)")
        r.raise_for_status()
        return ET.fromstring(r.text)

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        try:
            root = self._get_xml("/status/sessions")
            sessions = []
            for s in root:
                user_el  = s.find("User")
                player_el = s.find("Player")
                sessions.append({
                    "title":  s.get("title", s.get("grandparentTitle", "")),
                    "type":   s.get("type", ""),
                    "user":   user_el.get("title", "") if user_el is not None else "",
                    "player": player_el.get("title", "") if player_el is not None else "",
                    "state":  player_el.get("state", "") if player_el is not None else "",
                })
            return sessions
        except PermissionError as e:
            logging.warning(str(e))
            return []
        except Exception as e:
            logging.debug(f"Error getting Plex sessions: {e}")
            return []

    def get_library_stats(self) -> List[Dict[str, Any]]:
        try:
            root = self._get_xml("/library/sections")
            stats = []
            for section in root:
                stats.append({
                    "title": section.get("title", ""),
                    "type":  section.get("type", ""),
                    "count": int(section.get("count", 0)),
                    "key":   section.get("key", ""),
                })
            return stats
        except PermissionError as e:
            logging.warning(str(e))
            return []
        except Exception as e:
            logging.debug(f"Error getting Plex library stats: {e}")
            return []

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "health_check": lambda: {"healthy": self.health_check()},
            "get_sessions": lambda: {"sessions": self.get_active_sessions()},
            "get_library_stats": lambda: {"libraries": self.get_library_stats()},
        }
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        try:
            result = handler()
            return {"success": True, **result}
        except Exception as e:
            logging.error(f"Error executing Plex action '{action}': {e}")
            return {"success": False, "error": str(e)}
