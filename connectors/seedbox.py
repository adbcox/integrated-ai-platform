from __future__ import annotations

import os
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseConnector

# Direct IP — no DNS needed
_SEEDBOX_IP = "193.163.71.22"


class SeedboxConnector(BaseConnector):
    """
    SFTP connector for monitoring active downloads on the remote seedbox (seedit4me).

    Connects via SSH/SFTP (password or key) to the seedbox server and lists
    download directories to detect in-progress and recently completed transfers.

    Default target: 193.163.71.22:2088 (seedit4me service, direct IP)
    Auth: password via SEEDBOX_PASSWORD or SSH key via SEEDBOX_KEY_PATH.

    Set SEEDBOX_HOST=DISABLED to skip all connection attempts and return
    {"status": "disabled"} immediately.

    Falls back gracefully when unreachable:
      - Connection refused / timeout → {"status": "offline"}
      - No credentials → {"status": "not_configured"}
    """

    # Directories to probe on the seedbox
    WATCH_DIRS = [
        "/home/seedit4me/rwatch",            # blackhole (torrent files drop here)
        "/home/seedit4me/torrents/rtorrent", # main download dir (files land here)
    ]

    # Directories used only as a blackhole — .torrent drops, not actual media
    BLACKHOLE_DIRS = {"/home/seedit4me/rwatch"}

    # Tight connect timeout — prevents pipeline stalls
    _CONNECT_TIMEOUT = 8

    def __init__(self, host: str = "", user: str = "", port: int = 0,
                 password: str = "", key_path: str = ""):
        super().__init__()
        self.host     = host     or os.environ.get("SEEDBOX_HOST", _SEEDBOX_IP)
        self.user     = user     or os.environ.get("SEEDBOX_USER", "seedit4me")
        self.port     = int(os.environ.get("SEEDBOX_PORT", port or 2088))
        self.password = password or os.environ.get("SEEDBOX_PASSWORD", "2vraVAYcSF3uSIIdlF2U5ggw1OcgkEshSw")
        self.key_path = key_path or os.environ.get("SEEDBOX_KEY_PATH",
                            str(Path.home() / ".ssh" / "id_ed25519"))

    @property
    def _disabled(self) -> bool:
        return self.host.upper() in ("DISABLED", "NONE", "")

    def _resolve_host(self) -> str:
        """Return the host to connect to. Host is already an IP; simple passthrough."""
        if self._disabled:
            return ""
        return self.host

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

    def _ssh_client(self):
        """Return an authenticated paramiko SSHClient or raise."""
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = self._resolve_host()
        connect_kwargs: Dict[str, Any] = dict(
            hostname=host, port=self.port, username=self.user,
            timeout=self._CONNECT_TIMEOUT,
        )
        key_file = Path(self.key_path)
        if self.password:
            connect_kwargs["password"] = self.password
            connect_kwargs["allow_agent"] = False
            connect_kwargs["look_for_keys"] = False
        elif key_file.exists():
            connect_kwargs["key_filename"] = str(key_file)
        else:
            raise ConnectionError(
                f"No SEEDBOX_PASSWORD set and no SSH key at {self.key_path}."
            )

        client.connect(**connect_kwargs)
        return client

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
        """
        List files in a directory, return file metadata including active/completed flags.

        Fields per entry:
            name, size_bytes, size_gb, modified (ISO), age_hours, is_dir,
            in_blackhole, is_active, is_completed
        """
        in_blackhole = path in self.BLACKHOLE_DIRS
        try:
            attrs = sftp.listdir_attr(path)
            files = []
            now = datetime.datetime.now().timestamp()
            for a in attrs:
                if a.filename.startswith("."):
                    continue
                mtime = a.st_mtime or 0
                age_hours = (now - mtime) / 3600
                size = a.st_size or 0
                name = a.filename

                # Active = has .part suffix OR less than 5 minutes old
                is_active = name.endswith(".part") or age_hours < (5 / 60)
                # Completed = not in blackhole, not active, non-zero size
                is_completed = not in_blackhole and not is_active and size > 0

                files.append({
                    "name":        name,
                    "size_bytes":  size,
                    "size_gb":     round(size / (1024**3), 2),
                    "modified":    datetime.datetime.fromtimestamp(mtime).isoformat() if mtime else "",
                    "age_hours":   round(age_hours, 1),
                    "is_dir":      bool(a.st_mode and (a.st_mode & 0o40000)),
                    "in_blackhole": in_blackhole,
                    "is_active":   is_active,
                    "is_completed": is_completed,
                })
            return sorted(files, key=lambda x: x["modified"], reverse=True)
        except Exception:
            return []

    def run_ssh_command(self, cmd: str) -> str:
        """
        Open an SSH connection, run a single command, return stdout (up to 2000 chars).
        Returns "" on any error.
        """
        try:
            client = self._ssh_client()
            _, stdout, _ = client.exec_command(cmd, timeout=15)
            output = stdout.read().decode("utf-8", errors="replace")
            client.close()
            return output[:2000]
        except Exception as e:
            logging.debug(f"Seedbox SSH command error ({cmd!r}): {e}")
            return ""

    def get_rclone_log(self) -> Dict[str, Any]:
        """
        Read the rclone log from the seedbox and parse basic stats.

        Tries ~/rclone.log first, then /var/log/rclone.log.

        Returns:
            {
                "last_sync":   ISO timestamp string or "",
                "running":     bool,
                "transferred": int   (files transferred in last visible run),
                "errors":      int,
                "log_tail":    str   (last 5 log lines),
            }
        """
        cmd = (
            "tail -50 ~/rclone.log 2>/dev/null || "
            "tail -50 /var/log/rclone.log 2>/dev/null || "
            "echo NOTFOUND"
        )
        raw = self.run_ssh_command(cmd)

        if not raw or raw.strip() == "NOTFOUND":
            return {
                "last_sync":   "",
                "running":     False,
                "transferred": 0,
                "errors":      0,
                "log_tail":    "",
            }

        lines = raw.splitlines()
        last_sync = ""
        running = False
        transferred = 0
        errors = 0

        for line in lines:
            # rclone log lines look like: 2024/01/15 12:34:56 INFO ...
            # Detect a running sync
            if "Transferred:" in line and "ETA" in line:
                running = True
            # Detect completed sync stats line: "Transferred:   5 / 5, 100%"
            if "Transferred:" in line and "," in line:
                try:
                    part = line.split("Transferred:")[1].strip()
                    num_str = part.split("/")[0].strip().split()[0]
                    transferred = int(num_str)
                except Exception:
                    pass
            # Errors line
            if "Errors:" in line:
                try:
                    errors = int(line.split("Errors:")[1].strip().split()[0])
                except Exception:
                    pass
            # Capture timestamp from any INFO/ERROR line
            parts = line.split()
            if len(parts) >= 2:
                date_part = parts[0]  # e.g. 2024/01/15
                time_part = parts[1]  # e.g. 12:34:56
                if "/" in date_part and ":" in time_part:
                    try:
                        ts_str = f"{date_part} {time_part}".replace("/", "-")
                        last_sync = datetime.datetime.strptime(
                            ts_str, "%Y-%m-%d %H:%M:%S"
                        ).isoformat()
                    except Exception:
                        pass

        log_tail = "\n".join(lines[-5:]) if lines else ""

        return {
            "last_sync":   last_sync,
            "running":     running,
            "transferred": transferred,
            "errors":      errors,
            "log_tail":    log_tail,
        }

    def get_active_downloads(self) -> Dict[str, Any]:
        """
        List files in download directories, categorized as active / completed / blackhole.

        Returns:
            {
                "status": "connected",
                "active":    [{"name", "size_gb", "dir"}],         # .part or < 5min
                "completed": [{"name", "size_gb", "age_hours", "dir", "ready_for_sync"}],
                "blackhole": [{"name", "size_bytes"}],              # rwatch .torrent files
                "active_count":    int,
                "completed_count": int,
                "blackhole_count": int,
                "total_size_gb":   float,   # all non-dir files
                "completed_size_gb": float,
                # backwards-compat keys:
                "recent_files": int,  # = completed_count
                "total_files":  int,  # = active_count + completed_count
                "files":        list, # = completed list (top 20)
            }

        Never raises — all failure modes return a status dict.
        """
        if self._disabled:
            return {
                "status": "disabled",
                "message": "Seedbox disabled (SEEDBOX_HOST=DISABLED)",
                "files": [],
            }

        try:
            client, sftp = self._sftp()
            active_files: List[Dict[str, Any]] = []
            completed_files: List[Dict[str, Any]] = []
            blackhole_files: List[Dict[str, Any]] = []
            all_non_dir: List[Dict[str, Any]] = []

            for d in self.WATCH_DIRS:
                entries = self._list_dir(sftp, d)
                for f in entries:
                    f["dir"] = d
                    if f["is_dir"]:
                        continue
                    all_non_dir.append(f)
                    if f["in_blackhole"]:
                        blackhole_files.append({
                            "name":       f["name"],
                            "size_bytes": f["size_bytes"],
                        })
                    elif f["is_active"]:
                        active_files.append({
                            "name":    f["name"],
                            "size_gb": f["size_gb"],
                            "dir":     d,
                        })
                    elif f["is_completed"]:
                        completed_files.append({
                            "name":           f["name"],
                            "size_gb":        f["size_gb"],
                            "age_hours":      f["age_hours"],
                            "dir":            d,
                            "ready_for_sync": True,
                        })

            sftp.close()
            client.close()

            total_bytes = sum(f["size_bytes"] for f in all_non_dir)
            completed_bytes = sum(
                f["size_bytes"] for f in all_non_dir if f["is_completed"]
            )

            completed_top20 = completed_files[:20]

            return {
                "status":            "connected",
                "active":            active_files,
                "completed":         completed_files,
                "blackhole":         blackhole_files,
                "active_count":      len(active_files),
                "completed_count":   len(completed_files),
                "blackhole_count":   len(blackhole_files),
                "total_size_gb":     round(total_bytes / (1024**3), 2),
                "completed_size_gb": round(completed_bytes / (1024**3), 2),
                # backwards-compat
                "recent_files": len(completed_files),
                "total_files":  len(active_files) + len(completed_files),
                "files":        completed_top20,
            }

        except ConnectionError as e:
            return {"status": "not_configured", "message": str(e), "files": []}
        except ImportError:
            return {"status": "needs_paramiko",
                    "message": "pip install paramiko", "files": []}
        except OSError as e:
            err_str = str(e)
            if "nodename nor servname" in err_str or "Name or service not known" in err_str:
                logging.warning(f"Seedbox DNS resolution failed: {e}")
                return {"status": "offline",
                        "message": "DNS resolution failed — seedbox unreachable", "files": []}
            logging.warning(f"Seedbox network error: {e}")
            return {"status": "offline",
                    "message": f"Network error: {err_str[:120]}", "files": []}
        except Exception as e:
            logging.error(f"Seedbox get_active_downloads error: {e}")
            return {"status": "error", "message": str(e)[:120], "files": []}

    def get_queue_size(self) -> Dict[str, Any]:
        """Total size of all files in download directories."""
        result = self.get_active_downloads()
        return {
            "status":       result.get("status"),
            "total_files":  result.get("total_files", 0),
            "total_size_gb": result.get("total_size_gb", 0),
        }

    def get_recent_completions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Completed files modified in the last N hours."""
        result = self.get_active_downloads()
        if result.get("status") != "connected":
            return []
        return [f for f in result.get("completed", []) if f.get("age_hours", 999) <= hours]

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "health_check":         lambda: {"healthy": self.health_check()},
            "get_active_downloads": lambda: self.get_active_downloads(),
            "get_queue_size":       lambda: self.get_queue_size(),
            "get_recent_completions": lambda: {"completions": self.get_recent_completions(
                params.get("hours", 24))},
            "run_ssh_command":      lambda: {"output": self.run_ssh_command(
                params.get("cmd", ""))},
            "get_rclone_log":       lambda: self.get_rclone_log(),
        }
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        try:
            return {"success": True, **handler()}
        except Exception as e:
            logging.error(f"Seedbox execute error '{action}': {e}")
            return {"success": False, "error": str(e)}
