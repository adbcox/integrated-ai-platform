from __future__ import annotations

import os
import requests
import logging
from typing import List, Dict, Any, Optional

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

    def _api_prefix(self) -> str:
        """Prowlarr uses v1; Sonarr/Radarr use v3."""
        return "v1" if self.service_name.lower() == "prowlarr" else "v3"

    def health_check(self) -> bool:
        """Check if service is reachable. 401 counts as up (service running, just needs API key)."""
        try:
            v = self._api_prefix()
            response = self.session.get(f"{self.base_url}/api/{v}/system/status", timeout=5)
            return response.status_code in (200, 401)
        except Exception as e:
            logging.debug(f"Health check {self.service_name}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get system status including version."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/system/status", timeout=5)
            response.raise_for_status()
            data = response.json()
            return {"version": data.get("version", ""), "instance_name": data.get("instanceName", self.service_name)}
        except Exception:
            return {}

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get current download queue."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/queue", timeout=10)
            response.raise_for_status()
            return response.json().get("records", [])
        except Exception as e:
            logging.error(f"Error getting queue: {e}")
            return []

    def get_queue_count(self) -> int:
        """Return number of items in download queue."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/queue", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("totalRecords", len(data.get("records", [])))
        except Exception:
            return 0

    def get_calendar(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming releases/episodes."""
        import datetime
        try:
            today = datetime.date.today()
            end   = today + datetime.timedelta(days=days)
            v = self._api_prefix()
            response = self.session.get(
                f"{self.base_url}/api/{v}/calendar",
                params={"start": today.isoformat(), "end": end.isoformat()},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.debug(f"Error getting calendar: {e}")
            return []

    def get_series_count(self) -> Dict[str, int]:
        """Return monitored/total series counts (Sonarr only)."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/series", timeout=10)
            response.raise_for_status()
            series = response.json()
            monitored = sum(1 for s in series if s.get("monitored"))
            return {"total": len(series), "monitored": monitored}
        except Exception as e:
            logging.error(f"Error getting series count: {e}")
            return {"total": 0, "monitored": 0}

    def get_movie_count(self) -> Dict[str, int]:
        """Return monitored/total movie counts (Radarr only)."""
        try:
            response = self.session.get(f"{self.base_url}/api/v3/movie", timeout=10)
            response.raise_for_status()
            movies = response.json()
            monitored = sum(1 for m in movies if m.get("monitored"))
            downloaded = sum(1 for m in movies if m.get("hasFile"))
            return {"total": len(movies), "monitored": monitored, "downloaded": downloaded}
        except Exception as e:
            logging.error(f"Error getting movie count: {e}")
            return {"total": 0, "monitored": 0, "downloaded": 0}

    def get_indexer_count(self) -> Dict[str, int]:
        """Return enabled/total indexer counts (Prowlarr only)."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/indexer", timeout=10)
            response.raise_for_status()
            indexers = response.json()
            enabled = sum(1 for i in indexers if i.get("enable"))
            return {"total": len(indexers), "enabled": enabled}
        except Exception as e:
            logging.error(f"Error getting indexer count: {e}")
            return {"total": 0, "enabled": 0}

    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recently downloaded episodes from Sonarr history (eventType=3=Downloaded)."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v3/history",
                params={"pageSize": limit, "page": 1, "sortKey": "date",
                        "sortDirection": "descending", "eventType": 3},
                timeout=10,
            )
            response.raise_for_status()
            records = response.json().get("records", [])
            out = []
            for r in records[:limit]:
                series = r.get("series", {})
                ep = r.get("episode", {})
                out.append({
                    "series": series.get("title", r.get("sourceTitle", "")),
                    "season": ep.get("seasonNumber", 0),
                    "episode": ep.get("episodeNumber", 0),
                    "title": ep.get("title", ""),
                    "date": r.get("date", ""),
                    "quality": r.get("quality", {}).get("quality", {}).get("name", ""),
                })
            return out
        except Exception as e:
            logging.error(f"Error getting recent episodes: {e}")
            return []

    def get_recent_movies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recently downloaded movies from Radarr history (eventType=4=MovieFileImported)."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v3/history",
                params={"pageSize": limit, "page": 1, "sortKey": "date",
                        "sortDirection": "descending", "eventType": 4},
                timeout=10,
            )
            response.raise_for_status()
            records = response.json().get("records", [])
            out = []
            for r in records[:limit]:
                movie = r.get("movie", {})
                out.append({
                    "title": movie.get("title", r.get("sourceTitle", "")),
                    "year": movie.get("year", 0),
                    "date": r.get("date", ""),
                    "quality": r.get("quality", {}).get("quality", {}).get("name", ""),
                })
            return out
        except Exception as e:
            logging.error(f"Error getting recent movies: {e}")
            return []

    def get_upcoming_episodes(self, days: int = 7) -> List[Dict[str, Any]]:
        """Return upcoming episodes from Sonarr calendar."""
        import datetime
        try:
            today = datetime.date.today()
            end = today + datetime.timedelta(days=days)
            response = self.session.get(
                f"{self.base_url}/api/v3/calendar",
                params={"start": today.isoformat(), "end": end.isoformat(),
                        "includeSeries": "true"},
                timeout=10,
            )
            response.raise_for_status()
            items = response.json()
            out = []
            for ep in items:
                series = ep.get("series", {})
                out.append({
                    "series": series.get("title", ""),
                    "season": ep.get("seasonNumber", 0),
                    "episode": ep.get("episodeNumber", 0),
                    "title": ep.get("title", ""),
                    "air_date": ep.get("airDateUtc", ""),
                    "has_file": ep.get("hasFile", False),
                    "overview": ep.get("overview", "")[:120],
                })
            return sorted(out, key=lambda x: x["air_date"])
        except Exception as e:
            logging.error(f"Error getting upcoming episodes: {e}")
            return []

    def _command(self, name: str, **kwargs) -> bool:
        """POST a command to the service. Returns True on success."""
        v = self._api_prefix()
        try:
            r = self.session.post(
                f"{self.base_url}/api/{v}/command",
                json={"name": name, **kwargs},
                timeout=15,
            )
            return r.status_code in (200, 201, 202)
        except Exception as e:
            logging.debug(f"Command {name} failed: {e}")
            return False

    def get_queue_details(self) -> List[Dict[str, Any]]:
        """Full queue with progress, status, error messages."""
        v = self._api_prefix()
        try:
            r = self.session.get(
                f"{self.base_url}/api/{v}/queue",
                params={"pageSize": 100, "includeUnknownSeriesItems": True,
                        "includeUnknownMovieItems": True},
                timeout=15,
            )
            r.raise_for_status()
            return r.json().get("records", [])
        except Exception as e:
            logging.debug(f"get_queue_details error: {e}")
            return []

    def get_missing_episodes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Monitored episodes that aired but have no file (Sonarr)."""
        try:
            r = self.session.get(
                f"{self.base_url}/api/v3/wanted/missing",
                params={"sortKey": "airDateUtc", "sortDirection": "descending",
                        "pageSize": limit, "monitored": True},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            total = data.get("totalRecords", 0)
            records = data.get("records", [])
            out = []
            for ep in records:
                series = ep.get("series", {})
                out.append({
                    "id":        ep.get("id"),
                    "series_id": ep.get("seriesId"),
                    "series":    series.get("title", ep.get("seriesTitle", "")),
                    "season":    ep.get("seasonNumber", 0),
                    "episode":   ep.get("episodeNumber", 0),
                    "title":     ep.get("title", ""),
                    "air_date":  ep.get("airDateUtc", ""),
                })
            return out, total
        except Exception as e:
            logging.debug(f"get_missing_episodes error: {e}")
            return [], 0

    def get_missing_movies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Monitored movies without files (Radarr)."""
        try:
            r = self.session.get(f"{self.base_url}/api/v3/movie", timeout=15)
            r.raise_for_status()
            all_movies = r.json()
            missing = [m for m in all_movies if m.get("monitored") and not m.get("hasFile")]
            total = len(missing)
            out = []
            for m in missing[:limit]:
                out.append({
                    "id":       m.get("id"),
                    "title":    m.get("title", ""),
                    "year":     m.get("year", 0),
                    "air_date": m.get("digitalRelease") or m.get("inCinemas") or "",
                    "status":   m.get("status", ""),
                })
            return out, total
        except Exception as e:
            logging.debug(f"get_missing_movies error: {e}")
            return [], 0

    def search_missing_all(self) -> bool:
        """Trigger search for all missing monitored items."""
        name = "missingEpisodeSearch" if self.service_name == "sonarr" else "missingMoviesSearch"
        return self._command(name)

    def search_by_ids(self, ids: List[int]) -> bool:
        """Trigger search for specific episode/movie IDs."""
        if self.service_name == "sonarr":
            return self._command("EpisodeSearch", episodeIds=ids)
        else:
            return self._command("MoviesSearch", movieIds=ids)

    def remove_from_queue(self, queue_id: int, blacklist: bool = False) -> bool:
        """Remove an item from the download queue."""
        v = self._api_prefix()
        try:
            r = self.session.delete(
                f"{self.base_url}/api/{v}/queue/{queue_id}",
                params={"removeFromClient": "true",
                        "blacklist": "true" if blacklist else "false"},
                timeout=10,
            )
            return r.status_code in (200, 202, 204)
        except Exception as e:
            logging.debug(f"remove_from_queue error: {e}")
            return False

    def get_history_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Recent activity (all event types)."""
        v = self._api_prefix()
        try:
            r = self.session.get(
                f"{self.base_url}/api/{v}/history",
                params={"pageSize": limit, "page": 1,
                        "sortKey": "date", "sortDirection": "descending"},
                timeout=10,
            )
            r.raise_for_status()
            return r.json().get("records", [])
        except Exception:
            return []

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on service."""
        actions = {
            "health_check": lambda: {"healthy": self.health_check()},
            "get_queue": lambda: {"queue": self.get_queue()},
            "get_calendar": lambda: {"calendar": self.get_calendar(params.get("days", 7))},
            "get_series_count": lambda: self.get_series_count(),
            "get_movie_count": lambda: self.get_movie_count(),
            "get_indexer_count": lambda: self.get_indexer_count(),
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
