from __future__ import annotations

import os
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List

import yaml


class MediaDomain:
    """Media Domain: Manages *Arr stack, Plex, and seedbox download monitoring."""

    def __init__(self):
        config = self._load_config()
        self.config = config
        self.enabled = config.get("enabled", False)
        params = config.get("parameters", {})
        self.sonarr_url   = os.environ.get("SONARR_URL",   params.get("sonarr_url",   "http://192.168.10.201:8989"))
        self.radarr_url   = os.environ.get("RADARR_URL",   params.get("radarr_url",   "http://192.168.10.201:7878"))
        self.prowlarr_url = os.environ.get("PROWLARR_URL", params.get("prowlarr_url", "http://192.168.10.201:9696"))
        self.plex_url     = os.environ.get("PLEX_URL",     params.get("plex_url",     "http://192.168.10.201:32400"))
        self.qnap_url     = os.environ.get("QNAP_URL",     params.get("qnap_url",     "http://192.168.10.201"))
        self.sonarr_key   = os.environ.get("SONARR_API_KEY",  "")
        self.radarr_key   = os.environ.get("RADARR_API_KEY",  "")
        self.prowlarr_key = os.environ.get("PROWLARR_API_KEY","")
        self.plex_token   = os.environ.get("PLEX_TOKEN",      "")

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "domains.yaml"
        if not config_path.exists():
            return {"enabled": False, "parameters": {}}
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
            return data.get("MediaDomain", {"enabled": False, "parameters": {}})

    def _sonarr(self):
        from connectors.arr_stack import ArrStackConnector
        return ArrStackConnector("sonarr", self.sonarr_url, self.sonarr_key)

    def _radarr(self):
        from connectors.arr_stack import ArrStackConnector
        return ArrStackConnector("radarr", self.radarr_url, self.radarr_key)

    def _prowlarr(self):
        from connectors.arr_stack import ArrStackConnector
        return ArrStackConnector("prowlarr", self.prowlarr_url, self.prowlarr_key)

    def _plex(self):
        from connectors.plex import PlexConnector
        return PlexConnector(self.plex_url, self.plex_token)

    def _qnap(self):
        from connectors.qnap import QNAPConnector
        return QNAPConnector(base_url=self.qnap_url)

    def _seedbox(self):
        from connectors.seedbox import SeedboxConnector
        return SeedboxConnector()

    def _seedbox_safe(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Call seedbox.get_active_downloads() with a wall-clock timeout.

        Runs in a thread so DNS hangs (which ignore socket timeouts) can't
        block the pipeline. Returns a degraded dict on timeout or any error.
        """
        from connectors.seedbox import SeedboxConnector
        sb = SeedboxConnector()
        if sb._disabled:
            return {"status": "disabled", "message": "Seedbox disabled (SEEDBOX_HOST=DISABLED)", "files": []}
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(sb.get_active_downloads)
                return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return {"status": "offline", "message": f"Seedbox timed out after {timeout}s", "files": []}
        except Exception as e:
            return {"status": "error", "message": str(e)[:120], "files": []}

    def health_check(self) -> Dict[str, Any]:
        """Check reachability of all media services."""
        sb = self._seedbox_safe(timeout=10.0)
        return {
            "sonarr":   self._sonarr().health_check(),
            "radarr":   self._radarr().health_check(),
            "prowlarr": self._prowlarr().health_check(),
            "plex":     self._plex().health_check(),
            "seedbox":  sb.get("status") == "connected",
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return combined stats for all media services."""
        sonarr   = self._sonarr()
        radarr   = self._radarr()
        prowlarr = self._prowlarr()
        plex     = self._plex()
        seedbox  = self._seedbox()

        sonarr_up   = sonarr.health_check()
        radarr_up   = radarr.health_check()
        prowlarr_up = prowlarr.health_check()
        plex_up     = plex.health_check()

        stats: Dict[str, Any] = {
            "health": {
                "sonarr":   sonarr_up,
                "radarr":   radarr_up,
                "prowlarr": prowlarr_up,
                "plex":     plex_up,
            }
        }

        if sonarr_up:
            series = sonarr.get_series_count()
            stats["sonarr"] = {
                "series_total":     series["total"],
                "series_monitored": series["monitored"],
                "queue":            sonarr.get_queue_count(),
                "upcoming":         len(sonarr.get_calendar(days=7)),
            }
        else:
            stats["sonarr"] = {"error": "unreachable"}

        if radarr_up:
            movies = radarr.get_movie_count()
            stats["radarr"] = {
                "movies_total":      movies["total"],
                "movies_monitored":  movies["monitored"],
                "movies_downloaded": movies["downloaded"],
                "queue":             radarr.get_queue_count(),
            }
        else:
            stats["radarr"] = {"error": "unreachable"}

        if prowlarr_up:
            indexers = prowlarr.get_indexer_count()
            stats["prowlarr"] = {
                "indexers_total":   indexers["total"],
                "indexers_enabled": indexers["enabled"],
            }
        else:
            stats["prowlarr"] = {"error": "unreachable"}

        if plex_up:
            sessions  = plex.get_active_sessions()
            libraries = plex.get_library_stats()
            stats["plex"] = {
                "active_streams": len(sessions),
                "sessions":       sessions,
                "libraries":      libraries,
            }
        else:
            stats["plex"] = {"error": "unreachable"}

        # Seedbox — bounded by wall-clock timeout; never blocks other services
        sb = self._seedbox_safe(timeout=10.0)
        stats["seedbox"] = sb
        stats["health"]["seedbox"] = sb.get("status") == "connected"

        # QNAP storage — graceful on unavailable
        qnap = self._qnap()
        qnap_storage = qnap.get_storage_stats()
        stats["qnap"] = qnap_storage
        stats["health"]["qnap"] = qnap_storage.get("status") == "connected"

        return stats

    def get_downloads(self) -> Dict[str, Any]:
        """Return current seedbox download activity."""
        return self._seedbox_safe(timeout=10.0)

    def get_seedbox_status(self) -> Dict[str, Any]:
        """
        Rich seedbox status: active downloads, completed files ready for sync,
        blackhole queue, rclone log, and optional Flood torrent data.
        """
        sb = self._seedbox_safe(timeout=12.0)
        status = sb.get("status", "unknown")

        result: Dict[str, Any] = {
            "status":          status,
            "active_count":    sb.get("active_count",    0),
            "completed_count": sb.get("completed_count", 0),
            "blackhole_count": sb.get("blackhole_count", 0),
            "total_size_gb":   sb.get("total_size_gb",  0),
            "completed_size_gb": sb.get("completed_size_gb", 0),
            "active":          sb.get("active",    []),
            "completed":       sb.get("completed", [])[:10],
            "blackhole":       sb.get("blackhole", []),
            # backwards-compat
            "recent_files":    sb.get("recent_files", 0),
            "total_files":     sb.get("total_files",  0),
            "files":           sb.get("files",        []),
        }

        if status != "connected":
            result["message"] = sb.get("message", "")
            return result

        # Rclone log (SSH command — best-effort, never blocks)
        try:
            from connectors.seedbox import SeedboxConnector
            sc = SeedboxConnector()
            rclone = sc.get_rclone_log()
            result["rclone"] = rclone
        except Exception:
            result["rclone"] = {}

        # Flood torrent data (optional — skip if not installed)
        try:
            from connectors.flood_api import FloodAPI
            flood_url = os.environ.get("FLOOD_URL", f"http://{sc.host}:3000")
            flood = FloodAPI(url=flood_url)
            if flood.health_check():
                result["flood"] = flood.get_all_status()
        except Exception:
            pass

        return result

    def get_upcoming(self, days: int = 7) -> List[Dict[str, Any]]:
        """Return upcoming episodes from Sonarr calendar."""
        sonarr = self._sonarr()
        if not sonarr.health_check():
            return []
        items = sonarr.get_calendar(days=days)
        return [
            {
                "title":    i.get("series", {}).get("title", i.get("title", "")),
                "episode":  f"S{i.get('seasonNumber', 0):02d}E{i.get('episodeNumber', 0):02d}",
                "air_date": i.get("airDateUtc", ""),
            }
            for i in items[:10]
        ]
