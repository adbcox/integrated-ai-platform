"""Flood rTorrent web UI connector — REST API client."""
from __future__ import annotations

import json
import os
import logging
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List, Optional


class FloodAPI:
    """
    Client for the Flood rTorrent web UI (https://github.com/jesec/flood).

    Flood exposes a JSON REST API at http://{host}:{port}/api/.
    Requires session-cookie auth: POST /api/auth/authenticate first,
    then use the returned cookie for subsequent requests.

    Falls back gracefully if Flood is not installed — returns {"status": "not_available"}.

    Env vars (or pass to __init__):
        FLOOD_URL       default http://localhost:3000
        FLOOD_USERNAME  default admin
        FLOOD_PASSWORD  (required)
    """

    def __init__(self, url: str = "", username: str = "", password: str = ""):
        self.base_url = (url or os.environ.get("FLOOD_URL", "http://localhost:3000")).rstrip("/")
        self.username = username or os.environ.get("FLOOD_USERNAME", "admin")
        self.password = password or os.environ.get("FLOOD_PASSWORD", "")
        self._cookie: Optional[str] = None

    def _request(self, method: str, path: str, data: Any = None,
                 authenticated: bool = True) -> dict:
        """Make a request to Flood API. Returns parsed JSON or raises."""
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
        }
        if authenticated and self._cookie:
            headers["Cookie"] = self._cookie
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read()
                # Capture Set-Cookie on auth responses
                cookie = r.headers.get("Set-Cookie", "")
                if cookie:
                    self._cookie = cookie.split(";")[0]
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Flood HTTP {e.code} {method} {path}: {e.read().decode()[:200]}"
            ) from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Flood unreachable at {self.base_url}: {e.reason}"
            ) from e

    def authenticate(self) -> bool:
        """Authenticate and store session cookie. Returns True on success."""
        if not self.password:
            return False
        try:
            self._request(
                "POST", "/api/auth/authenticate",
                {"username": self.username, "password": self.password},
                authenticated=False,
            )
            return bool(self._cookie)
        except Exception:
            return False

    def health_check(self) -> bool:
        """Returns True if Flood is running and authentication works."""
        try:
            self._request("GET", "/api/auth/verify", authenticated=False)
            return True
        except ConnectionError:
            return False
        except Exception:
            # 401 means Flood is up, just not authenticated
            return True

    def get_torrents(self) -> List[Dict[str, Any]]:
        """
        Return list of active torrents with status, progress, speed, ETA.
        Authenticates if needed. Returns [] if Flood unavailable.
        """
        if not self._cookie:
            if not self.authenticate():
                return []
        try:
            data = self._request("GET", "/api/torrents")
            torrents = data.get("torrents", {})
            result: List[Dict[str, Any]] = []
            for hash_id, t in torrents.items():
                size_bytes = t.get("sizeBytes", 0)
                completed_bytes = t.get("bytesDone", 0)
                pct = round(completed_bytes / size_bytes * 100, 1) if size_bytes > 0 else 0
                speed = t.get("downRate", 0)
                eta_secs = t.get("eta", -1)
                result.append({
                    "hash":       hash_id,
                    "name":       t.get("name", ""),
                    "status":     t.get("status", []),
                    "size_gb":    round(size_bytes / (1024**3), 2),
                    "done_gb":    round(completed_bytes / (1024**3), 2),
                    "pct":        pct,
                    "speed_mbps": round(speed / (1024**2), 2),
                    "eta_secs":   eta_secs,
                    "seeds":      t.get("seedsConnected", 0),
                    "peers":      t.get("peersConnected", 0),
                    "label":      (t.get("tags") or [""])[0],
                    "path":       t.get("directory", ""),
                    "added":      t.get("dateAdded", 0),
                })
            return sorted(result, key=lambda x: x["added"], reverse=True)
        except Exception as e:
            logging.warning(f"Flood get_torrents error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Return transfer stats: speeds, session totals, uptime."""
        if not self._cookie:
            if not self.authenticate():
                return {"status": "not_authenticated"}
        try:
            self._request("GET", "/api/client/connection-test")
            stats = self._request("GET", "/api/transfer-data")
            speeds = stats.get("transferData", {})
            return {
                "status":        "connected",
                "down_mbps":     round(speeds.get("downSpeed", 0) / (1024**2), 2),
                "up_mbps":       round(speeds.get("upSpeed", 0) / (1024**2), 2),
                "down_total_gb": round(speeds.get("downTotal", 0) / (1024**3), 2),
                "up_total_gb":   round(speeds.get("upTotal", 0) / (1024**3), 2),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)[:120]}

    def get_torrent_files(self, torrent_hash: str) -> List[Dict[str, Any]]:
        """Return file listing for a specific torrent by hash."""
        if not self._cookie:
            if not self.authenticate():
                return []
        try:
            data = self._request("GET", f"/api/torrents/{torrent_hash}/contents")
            files = data.get("contents", [])
            return [
                {
                    "path":     f.get("path", ""),
                    "size_gb":  round(f.get("sizeBytes", 0) / (1024**3), 3),
                    "pct":      f.get("percentComplete", 0),
                    "priority": f.get("priority", 0),
                }
                for f in files
            ]
        except Exception:
            return []

    def get_all_status(self) -> Dict[str, Any]:
        """Combined status: torrents + stats in one call."""
        if not self.health_check():
            return {"status": "not_available", "torrents": [], "stats": {}}
        torrents = self.get_torrents()
        stats    = self.get_stats()
        active   = [t for t in torrents if "downloading" in t.get("status", [])]
        seeding  = [t for t in torrents if "seeding"     in t.get("status", [])]
        return {
            "status":        "connected",
            "torrents":      torrents,
            "active_count":  len(active),
            "seeding_count": len(seeding),
            "total_count":   len(torrents),
            "stats":         stats,
        }
