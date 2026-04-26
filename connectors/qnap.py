from __future__ import annotations

import os
import logging
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, Any

import requests

from .base import BaseConnector


class QNAPConnector(BaseConnector):
    """
    QNAP NAS connector — storage stats via QTS API with SSH fallback.

    Uses QTS authLogin.cgi to get a session ID, then queries:
      /cgi-bin/filemanager/utilRequest.cgi for volume/share stats.

    SSH fallback: runs `df -k /share` if QTS API is unreachable.
    """

    def __init__(self, base_url: str = "", username: str = "", password: str = ""):
        super().__init__()
        self.base_url  = (base_url or os.environ.get("QNAP_URL", "http://192.168.10.201")).rstrip("/")
        self.username  = username  or os.environ.get("QNAP_USER", "admin")
        self.password  = password  or os.environ.get("QNAP_PASS", "")
        self._sid: str = ""

    # ── Authentication ────────────────────────────────────────────────────────

    def _login(self) -> bool:
        """Obtain a QTS session ID.  Returns True on success."""
        try:
            pwd_hash = hashlib.md5(self.password.encode()).hexdigest()
            r = requests.get(
                f"{self.base_url}/cgi-bin/authLogin.cgi",
                params={"user": self.username, "pwd": pwd_hash, "serviceKey": "1"},
                timeout=8,
            )
            r.raise_for_status()
            root = ET.fromstring(r.text)
            sid = root.findtext("authSid") or ""
            if sid and sid != "0":
                self._sid = sid
                return True
            # Some QTS versions return plain-text password
            r2 = requests.get(
                f"{self.base_url}/cgi-bin/authLogin.cgi",
                params={"user": self.username, "pwd": self.password, "serviceKey": "1"},
                timeout=8,
            )
            root2 = ET.fromstring(r2.text)
            sid2 = root2.findtext("authSid") or ""
            if sid2 and sid2 != "0":
                self._sid = sid2
                return True
            return False
        except Exception as e:
            logging.debug(f"QNAP login error: {e}")
            return False

    # ── Health check ──────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        try:
            r = requests.get(self.base_url, timeout=5)
            return r.status_code < 500
        except Exception:
            return False

    # ── Storage stats ─────────────────────────────────────────────────────────

    def get_storage_stats(self) -> Dict[str, Any]:
        """Return total/used/free GB and percent for /share volume."""
        result = self._storage_via_qts()
        if result.get("status") == "connected":
            return result
        return self._storage_via_ssh()

    def _storage_via_qts(self) -> Dict[str, Any]:
        try:
            if not self._sid and not self._login():
                return {"status": "auth_failed"}
            r = requests.get(
                f"{self.base_url}/cgi-bin/filemanager/utilRequest.cgi",
                params={"func": "stat_file_system", "sid": self._sid},
                timeout=10,
            )
            r.raise_for_status()
            root = ET.fromstring(r.text)
            # Look for /share or the first volume
            best = None
            for vol in root.iter("volume"):
                mp = vol.findtext("mount_point") or vol.findtext("path") or ""
                if "/share" in mp or best is None:
                    best = vol
            if best is None:
                return {"status": "no_volume"}
            def _kb(tag):
                try:
                    return int(best.findtext(tag) or 0)
                except ValueError:
                    return 0
            total_kb = _kb("size_total") or _kb("total_size") or _kb("capacity")
            used_kb  = _kb("size_used")  or _kb("used_size")  or _kb("used")
            free_kb  = _kb("size_free")  or _kb("free_size")  or _kb("free")
            if not free_kb and total_kb and used_kb:
                free_kb = total_kb - used_kb
            if not total_kb:
                return {"status": "parse_error"}
            return {
                "status":   "connected",
                "total_gb": round(total_kb / (1024**2), 1),
                "used_gb":  round(used_kb  / (1024**2), 1),
                "free_gb":  round(free_kb  / (1024**2), 1),
                "used_pct": round(used_kb / total_kb * 100) if total_kb else 0,
                "source":   "qts_api",
            }
        except Exception as e:
            logging.debug(f"QTS storage stats error: {e}")
            return {"status": "error", "message": str(e)}

    def _storage_via_ssh(self) -> Dict[str, Any]:
        """Fallback: SSH to QNAP and run df."""
        try:
            import paramiko
            host = self.base_url.split("//")[-1].split(":")[0]
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                host, port=22, username=self.username,
                password=self.password, timeout=8,
                allow_agent=False, look_for_keys=False,
            )
            _, stdout, _ = client.exec_command(
                "df -k /share/download 2>/dev/null || df -k /share 2>/dev/null || df -k /"
            )
            output = stdout.read().decode(errors="replace")
            client.close()
            # df can wrap filesystem names onto the next line; rejoin them
            joined = " ".join(output.split())  # flatten to one line of tokens
            tokens = joined.split()
            # Scan for 4+ consecutive numeric tokens (1K-blocks, Used, Available, Use%)
            for i in range(len(tokens) - 3):
                try:
                    total_kb = int(tokens[i])
                    used_kb  = int(tokens[i+1])
                    avail_kb = int(tokens[i+2])
                    if total_kb > 0 and total_kb > used_kb:
                        return {
                            "status":   "connected",
                            "total_gb": round(total_kb / (1024**2), 1),
                            "used_gb":  round(used_kb  / (1024**2), 1),
                            "free_gb":  round(avail_kb / (1024**2), 1),
                            "used_pct": round(used_kb / total_kb * 100),
                            "source":   "ssh_df",
                        }
                except ValueError:
                    continue
            return {"status": "parse_error"}
        except ImportError:
            return {"status": "needs_paramiko", "message": "pip install paramiko"}
        except Exception as e:
            logging.debug(f"QNAP SSH storage error: {e}")
            return {"status": "error", "message": str(e)}

    # ── Download folder stats ─────────────────────────────────────────────────

    def get_download_stats(self) -> Dict[str, Any]:
        """Check file counts in /share/download via SSH."""
        try:
            import paramiko
            host = self.base_url.split("//")[-1].split(":")[0]
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                host, port=22, username=self.username,
                password=self.password, timeout=8,
                allow_agent=False, look_for_keys=False,
            )
            sftp = client.open_sftp()
            counts: Dict[str, int] = {}
            for d in ["/share/download/rtorrent", "/share/download/sabnzbd",
                      "/share/download/rtorrent/completed", "/share/download"]:
                try:
                    entries = sftp.listdir(d)
                    counts[d] = len([e for e in entries if not e.startswith(".")])
                except Exception:
                    pass
            sftp.close()
            client.close()
            return {
                "status": "connected",
                "dirs": counts,
                "total_waiting": sum(counts.values()),
            }
        except ImportError:
            return {"status": "needs_paramiko"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _ssh_run(self, cmd: str, timeout: int = 10) -> str:
        """Run a command over SSH, return stdout."""
        import paramiko
        host = self.base_url.split("//")[-1].split(":")[0]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=22, username=self.username,
                       password=self.password, timeout=8,
                       allow_agent=False, look_for_keys=False)
        _, stdout, _ = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors="replace")
        client.close()
        return out

    def get_rclone_status(self) -> Dict[str, Any]:
        """Check rclone process state, last sync time, and pending file count."""
        try:
            # Run multiple checks in one SSH session
            import paramiko
            host = self.base_url.split("//")[-1].split(":")[0]
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=22, username=self.username,
                           password=self.password, timeout=8,
                           allow_agent=False, look_for_keys=False)

            # Is rclone running?
            _, out, _ = client.exec_command("pgrep -x rclone 2>/dev/null | wc -l")
            running = int(out.read().decode().strip() or "0") > 0

            # Find rclone log file (common QNAP locations)
            _, out, _ = client.exec_command(
                "ls -t /share/homes/admin/rclone*.log /share/homes/admin/logs/rclone*.log "
                "/var/log/rclone*.log /tmp/rclone*.log 2>/dev/null | head -1"
            )
            log_path = out.read().decode().strip()

            last_sync_ago = None
            last_sync_iso = None
            if log_path:
                _, out, _ = client.exec_command(
                    f"stat -c '%Y' {log_path} 2>/dev/null || stat -f '%m' {log_path} 2>/dev/null"
                )
                mtime_str = out.read().decode().strip()
                if mtime_str.isdigit():
                    import datetime
                    mtime = int(mtime_str)
                    now = int(datetime.datetime.now().timestamp())
                    ago_min = (now - mtime) // 60
                    last_sync_ago = ago_min
                    last_sync_iso = datetime.datetime.fromtimestamp(mtime).isoformat()

            # Count files pending in download directories
            _, out, _ = client.exec_command(
                "find /share/download -maxdepth 3 -type f "
                "! -name '*.part' ! -name '*.nzb' ! -name '*.torrent' 2>/dev/null | wc -l"
            )
            pending_files = int(out.read().decode().strip() or "0")

            # Disk usage of /share/download specifically
            _, out, _ = client.exec_command("du -sk /share/download 2>/dev/null | awk '{print $1}'")
            dl_kb = int(out.read().decode().strip() or "0")

            client.close()

            result: Dict[str, Any] = {
                "status":         "connected",
                "rclone_running": running,
                "pending_files":  pending_files,
                "download_gb":    round(dl_kb / (1024**2), 2),
                "last_sync_ago_min": last_sync_ago,
                "last_sync_iso":     last_sync_iso,
            }
            # Alert if last sync is stale
            if last_sync_ago is not None and last_sync_ago > 30:
                result["alert"] = f"rclone hasn't synced in {last_sync_ago} min"
            elif last_sync_ago is None and not running:
                result["alert"] = "rclone not running and no log found"
            return result
        except ImportError:
            return {"status": "needs_paramiko"}
        except Exception as e:
            logging.debug(f"rclone status error: {e}")
            return {"status": "error", "message": str(e)}

    def force_rclone_sync(self) -> Dict[str, Any]:
        """SSH to QNAP and trigger rclone sync script."""
        try:
            # Try common rclone script locations
            out = self._ssh_run(
                "ls /share/homes/admin/rclone_sync.sh "
                "/share/scripts/rclone_sync.sh "
                "/etc/config/autorun.sh 2>/dev/null | head -1"
            ).strip()
            script = out if out else None

            if script:
                self._ssh_run(f"nohup bash {script} > /tmp/rclone_manual.log 2>&1 &")
                return {"ok": True, "message": f"Started {script}"}
            else:
                # Generic: find rclone config and run manually
                cfg = self._ssh_run("ls ~/.config/rclone/rclone.conf 2>/dev/null").strip()
                if cfg:
                    self._ssh_run(
                        "nohup rclone sync remote: /share/download/completed "
                        "--log-file /tmp/rclone_manual.log "
                        "--transfers 4 --checkers 8 &"
                    )
                    return {"ok": True, "message": "Started rclone sync (generic)"}
                return {"ok": False, "message": "No rclone script or config found on QNAP"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        actions = {
            "health_check":       lambda: {"healthy": self.health_check()},
            "get_storage_stats":  lambda: self.get_storage_stats(),
            "get_download_stats": lambda: self.get_download_stats(),
        }
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        try:
            return {"success": True, **handler()}
        except Exception as e:
            return {"success": False, "error": str(e)}
