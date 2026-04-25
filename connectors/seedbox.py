from __future__ import annotations

import os
import logging
import socket
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseConnector

# Known good IP for seedit4me — used as fallback when hostname DNS fails
_SEEDBOX_IP_FALLBACK = "193.163.71.22"


class SeedboxConnector(BaseConnector):
    """
    SFTP connector for monitoring active downloads on the remote seedbox (seedit4me).

    Connects via SSH/SFTP (password or key) to the seedbox server and lists
    download directories to detect in-progress and recently completed transfers.

    Default target: 5.nl19.seedit4me:2088 (seedit4me service)
    Auth: password via SEEDBOX_PASSWORD or SSH key via SEEDBOX_KEY_PATH.

    Set SEEDBOX_HOST=DISABLED to skip all connection attempts and return
    {"status": "disabled"} immediately — prevents DNS hangs from cascading.

    Falls back gracefully when unreachable:
      - DNS failure → tries IP fallback (193.163.71.22) once
      - Connection refused / timeout → {"status": "offline"}
      - No credentials → {"status": "not_configured"}
    """

    # Candidate directories to probe on the seedbox (tries each, collects non-empty)
    WATCH_DIRS = [
        "/home/seedit4me",
        "/home/seedit4me/downloads",
        "/home/seedit4me/rtorrent",
        "/home/seedit4me/files",
        "/home/seedit4me/sabnzbd",
        "/media",
        "/data",
        "/downloads",
    ]

    # Tight connect timeout — DNS hangs block the pipeline otherwise
    _CONNECT_TIMEOUT = 8

    def __init__(self, host: str = "", user: str = "", port: int = 0,
                 password: str = "", key_path: str = ""):
        super().__init__()
        self.host     = host     or os.environ.get("SEEDBOX_HOST", "5.nl19.seedit4me")
        self.user     = user     or os.environ.get("SEEDBOX_USER", "seedit4me")
        self.port     = int(os.environ.get("SEEDBOX_PORT", port or 2088))
        self.password = password or os.environ.get("SEEDBOX_PASSWORD", "")
        self.key_path = key_path or os.environ.get("SEEDBOX_KEY_PATH",
                            str(Path.home() / ".ssh" / "id_ed25519"))

    @property
    def _disabled(self) -> bool:
        return self.host.upper() in ("DISABLED", "NONE", "")

    def _resolve_host(self) -> str:
        """Return the hostname to connect to, trying IP fallback on DNS failure."""
        if self._disabled:
            return ""
        try:
            socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
            return self.host
        except OSError:
            logging.info(f"Seedbox DNS failed for '{self.host}', trying IP fallback {_SEEDBOX_IP_FALLBACK}")
            return _SEEDBOX_IP_FALLBACK

    def _sftp(self, host_override: str = ""):
        """Return an authenticated paramiko SFTP session or raise."""
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = host_override or self._resolve_host()
        connect_kwargs: Dict[str, Any] = dict(
            hostname=host, port=self.port, username=self.user,
            timeout=self._CONNECT_TIMEOUT,
        )
        key_file = Path(self.key_path)
        if self.password:
            # Password auth is primary for remote seedbox
            connect_kwargs["password"] = self.password
            connect_kwargs["allow_agent"] = False
            connect_kwargs["look_for_keys"] = False
        elif key_file.exists():
            connect_kwargs["key_filename"] = str(key_file)
        else:
            raise ConnectionError(
                f"No SEEDBOX_PASSWORD set and no SSH key at {self.key_path}. "
                "Set SEEDBOX_PASSWORD in docker/.env."
            )

        client.connect(**connect_kwargs)
        return client, client.open_sftp()

    def health_check(self) -> bool:
        if self._disabled:
            return False
        try:
            client, sftp = self._sftp()
            sftp.close()
            client.close()
            return True
        except Exception as e:
            logging.debug(f"Seedbox health check failed: {e}")
            return False

    def _list_dir(self, sftp, path: str) -> List[Dict[str, Any]]:
        """List files in a directory, return file metadata."""
        try:
            attrs = sftp.listdir_attr(path)
            files = []
            now = datetime.datetime.now().timestamp()
            for a in attrs:
                if a.filename.startswith("."):
                    continue
                mtime = a.st_mtime or 0
                age_hours = (now - mtime) / 3600
                files.append({
                    "name": a.filename,
                    "size_bytes": a.st_size or 0,
                    "size_gb": round((a.st_size or 0) / (1024**3), 2),
                    "modified": datetime.datetime.fromtimestamp(mtime).isoformat() if mtime else "",
                    "age_hours": round(age_hours, 1),
                    "is_dir": bool(a.st_mode and (a.st_mode & 0o40000)),
                })
            return sorted(files, key=lambda x: x["modified"], reverse=True)
        except Exception:
            return []

    def get_active_downloads(self) -> Dict[str, Any]:
        """
        List files in download directories, infer active vs completed.
        Returns counts, sizes, and recent files.

        Never raises — all failure modes return a status dict so callers
        can continue without crashing the pipeline.
        """
        if self._disabled:
            return {"status": "disabled", "message": "Seedbox disabled (SEEDBOX_HOST=DISABLED)", "files": []}

        try:
            client, sftp = self._sftp()
            all_files: List[Dict[str, Any]] = []
            dirs_found: List[str] = []

            for d in self.WATCH_DIRS:
                files = self._list_dir(sftp, d)
                if files:
                    dirs_found.append(d)
                    for f in files:
                        f["dir"] = d
                    all_files.extend(files)

            sftp.close()
            client.close()

            # Files modified in last 24h = likely active or recent
            recent = [f for f in all_files if f["age_hours"] <= 24]
            total_bytes = sum(f["size_bytes"] for f in all_files if not f["is_dir"])
            recent_bytes = sum(f["size_bytes"] for f in recent if not f["is_dir"])

            return {
                "status": "connected",
                "dirs_monitored": dirs_found,
                "total_files": len([f for f in all_files if not f["is_dir"]]),
                "total_size_gb": round(total_bytes / (1024**3), 2),
                "recent_files": len([f for f in recent if not f["is_dir"]]),
                "recent_size_gb": round(recent_bytes / (1024**3), 2),
                "files": [f for f in recent if not f["is_dir"]][:20],
            }
        except ConnectionError as e:
            return {"status": "not_configured", "message": str(e), "files": []}
        except ImportError:
            return {"status": "needs_paramiko",
                    "message": "pip install paramiko", "files": []}
        except OSError as e:
            # DNS resolution failures, connection refused, network unreachable
            err_str = str(e)
            if "nodename nor servname" in err_str or "Name or service not known" in err_str:
                logging.warning(f"Seedbox DNS resolution failed: {e}")
                return {"status": "offline", "message": "DNS resolution failed — seedbox unreachable", "files": []}
            logging.warning(f"Seedbox network error: {e}")
            return {"status": "offline", "message": f"Network error: {err_str[:120]}", "files": []}
        except Exception as e:
            logging.error(f"Seedbox get_active_downloads error: {e}")
            return {"status": "error", "message": str(e)[:120], "files": []}

    def get_queue_size(self) -> Dict[str, Any]:
        """Total size of all files in download directories."""
        result = self.get_active_downloads()
        return {
            "status": result.get("status"),
            "total_files": result.get("total_files", 0),
            "total_size_gb": result.get("total_size_gb", 0),
        }

    def get_recent_completions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Files modified in the last N hours (likely recent completions)."""
        result = self.get_active_downloads()
        if result.get("status") != "connected":
            return []
        return [f for f in result.get("files", []) if f.get("age_hours", 999) <= hours]

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "health_check": lambda: {"healthy": self.health_check()},
            "get_active_downloads": lambda: self.get_active_downloads(),
            "get_queue_size": lambda: self.get_queue_size(),
            "get_recent_completions": lambda: {"completions": self.get_recent_completions(
                params.get("hours", 24))},
        }
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        try:
            return {"success": True, **handler()}
        except Exception as e:
            logging.error(f"Seedbox execute error '{action}': {e}")
            return {"success": False, "error": str(e)}
