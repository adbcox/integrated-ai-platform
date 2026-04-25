"""Media pipeline health checker — uses native *arr health APIs + QNAP SSH checks."""
from __future__ import annotations

import concurrent.futures
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))


@dataclass
class Issue:
    service:   str
    severity:  str          # "critical" | "warning" | "info"
    source:    str          # "arr_health" | "queue" | "disk" | "rclone" | "rootfolder" | "path"
    message:   str
    detail:    str = ""
    fixable:   bool = False
    fix_action: str = ""    # machine-readable fix key
    fix_data:  dict = field(default_factory=dict)


@dataclass
class HealthReport:
    issues:      list[Issue]
    checked_at:  float
    duration_s:  float
    services:    dict[str, bool]   # service → reachable

    @property
    def critical(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "critical"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def fixable(self) -> list[Issue]:
        return [i for i in self.issues if i.fixable]

    def as_dict(self) -> dict:
        return {
            "issues": [
                {
                    "service":    i.service, "severity": i.severity,
                    "source":     i.source,  "message":  i.message,
                    "detail":     i.detail,  "fixable":  i.fixable,
                    "fix_action": i.fix_action, "fix_data": i.fix_data,
                }
                for i in self.issues
            ],
            "checked_at":  self.checked_at,
            "duration_s":  round(self.duration_s, 2),
            "services":    self.services,
            "counts": {
                "total":    len(self.issues),
                "critical": len(self.critical),
                "warnings": len(self.warnings),
                "fixable":  len(self.fixable),
            },
        }


class MediaHealthChecker:
    """Run all health checks and return a HealthReport."""

    SEVERITY_MAP = {"error": "critical", "warning": "warning", "notice": "info", "ok": "info"}
    # Issues we can surface but not auto-fix
    KNOWN_NOISE = {"UpdateCheck", "RemovedMovieCheck"}

    def __init__(self) -> None:
        from connectors.arr_stack import ArrStackConnector
        from connectors.qnap import QNAPConnector

        self._sonarr   = ArrStackConnector(
            "sonarr",   os.environ.get("SONARR_URL",   "http://192.168.10.201:8989"),
                        os.environ.get("SONARR_API_KEY", ""))
        self._radarr   = ArrStackConnector(
            "radarr",   os.environ.get("RADARR_URL",   "http://192.168.10.201:7878"),
                        os.environ.get("RADARR_API_KEY", ""))
        self._prowlarr = ArrStackConnector(
            "prowlarr", os.environ.get("PROWLARR_URL", "http://192.168.10.201:9696"),
                        os.environ.get("PROWLARR_API_KEY", ""))
        self._qnap = QNAPConnector(
            os.environ.get("QNAP_URL",  "http://192.168.10.201"),
            os.environ.get("QNAP_USER", "admin"),
            os.environ.get("QNAP_PASS", ""))

    def _check_seedbox(self) -> list[Issue]:
        """Check seedbox connectivity — isolated with timeout so DNS failures don't cascade."""
        from connectors.seedbox import SeedboxConnector
        sb = SeedboxConnector()

        if sb._disabled:
            return [Issue("seedbox", "info", "reachability",
                          "Seedbox disabled (SEEDBOX_HOST=DISABLED) — set host to re-enable",
                          fixable=False)]

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(sb.get_active_downloads)
                result = fut.result(timeout=12.0)
        except concurrent.futures.TimeoutError:
            return [Issue("seedbox", "warning", "reachability",
                          "Seedbox check timed out (>12s) — possible DNS hang",
                          "Consider using IP address instead of hostname", fixable=False)]
        except Exception as exc:
            return [Issue("seedbox", "warning", "reachability",
                          f"Seedbox check error: {str(exc)[:100]}", fixable=False)]

        status = result.get("status", "unknown")
        if status == "connected":
            return []
        if status in ("disabled", "not_configured"):
            return [Issue("seedbox", "info", "reachability",
                          f"Seedbox not available: {result.get('message', status)}",
                          fixable=False)]
        # offline / error / dns failure
        return [Issue("seedbox", "warning", "reachability",
                      f"Seedbox degraded [{status}]: {result.get('message', '')[:100]}",
                      "Check SEEDBOX_HOST or use IP fallback 193.163.71.22",
                      fixable=False)]

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self) -> HealthReport:
        t0 = time.monotonic()
        issues: list[Issue] = []
        services: dict[str, bool] = {}

        for svc, connector in [("sonarr", self._sonarr), ("radarr", self._radarr),
                                ("prowlarr", self._prowlarr)]:
            up = connector.health_check()
            services[svc] = up
            if not up:
                issues.append(Issue(svc, "critical", "reachability",
                                    f"{svc} is unreachable", fixable=False))
                continue
            issues.extend(self._check_arr_health(connector, svc))
            issues.extend(self._check_arr_queue(connector, svc))
            if svc in ("sonarr", "radarr"):
                issues.extend(self._check_rootfolders(connector, svc))
                issues.extend(self._check_remote_path_mappings(connector, svc))

        up_qnap = self._qnap.health_check()
        services["qnap"] = up_qnap
        if up_qnap:
            issues.extend(self._check_qnap_storage())
            issues.extend(self._check_rclone())
        else:
            issues.append(Issue("qnap", "critical", "reachability",
                                "QNAP NAS is unreachable", fixable=False))

        # Seedbox: always check last — isolated with timeout, never blocks other checks
        seedbox_issues = self._check_seedbox()
        services["seedbox"] = not any(
            i.severity in ("critical", "warning") for i in seedbox_issues
        )
        issues.extend(seedbox_issues)

        return HealthReport(
            issues     = issues,
            checked_at = time.time(),
            duration_s = time.monotonic() - t0,
            services   = services,
        )

    # ── *Arr native health endpoint ───────────────────────────────────────────

    def _check_arr_health(self, connector, svc: str) -> list[Issue]:
        v = connector._api_prefix()
        try:
            r = connector.session.get(f"{connector.base_url}/api/{v}/health", timeout=8)
            r.raise_for_status()
            items = r.json()
        except Exception as exc:
            return [Issue(svc, "warning", "arr_health",
                          f"Could not fetch {svc} health: {exc}", fixable=False)]
        out = []
        for item in items:
            source = item.get("source", "")
            sev    = self.SEVERITY_MAP.get(item.get("type", "warning"), "warning")
            msg    = item.get("message", "")
            wiki   = item.get("wikiUrl", "")
            # Update warnings: not critical, not fixable
            if source == "UpdateCheck":
                out.append(Issue(svc, "info", "arr_health", msg, wiki, fixable=False))
                continue
            # Removed TMDb entry: manual cleanup only
            if source == "RemovedMovieCheck":
                out.append(Issue(svc, "warning", "arr_health", msg, wiki, fixable=False,
                                 fix_action="manual_cleanup"))
                continue
            # Missing root folder for collection
            if "RootFolder" in source or "Collection" in source:
                out.append(Issue(svc, sev, "arr_health", msg[:200], wiki, fixable=False,
                                 fix_action="fix_root_folder"))
                continue
            out.append(Issue(svc, sev, "arr_health", msg[:200], wiki, fixable=False))
        return out

    # ── Queue health ──────────────────────────────────────────────────────────

    def _check_arr_queue(self, connector, svc: str) -> list[Issue]:
        out = []
        try:
            items = connector.get_queue_details()
        except Exception:
            return []
        for item in items:
            tracked = item.get("trackedDownloadStatus", "ok")
            status  = item.get("status", "")
            title   = (item.get("title") or "")[:60]
            qid     = item.get("id")
            msgs    = [m.get("message", "") for m in item.get("statusMessages", [])]
            detail  = "; ".join(msgs)[:120] if msgs else tracked

            if tracked in ("warning", "error"):
                severity = "critical" if tracked == "error" else "warning"
                out.append(Issue(
                    svc, severity, "queue",
                    f"Download error: {title}",
                    detail, fixable=True,
                    fix_action="remove_and_requeue",
                    fix_data={"queue_id": qid, "service": svc},
                ))
            elif status == "downloading" and not item.get("timeleft") and not item.get("sizeleft"):
                out.append(Issue(
                    svc, "warning", "queue",
                    f"Stalled download: {title}",
                    "No progress or time remaining", fixable=True,
                    fix_action="remove_and_requeue",
                    fix_data={"queue_id": qid, "service": svc},
                ))
        return out

    # ── Root folder validation ────────────────────────────────────────────────

    def _check_rootfolders(self, connector, svc: str) -> list[Issue]:
        v = connector._api_prefix()
        try:
            r = connector.session.get(f"{connector.base_url}/api/{v}/rootfolder", timeout=8)
            r.raise_for_status()
            folders = r.json()
        except Exception:
            return []
        out = []
        for folder in folders:
            path = folder.get("path", "")
            ok   = folder.get("accessible", True)
            free = folder.get("freeSpace", 0)
            if not ok:
                out.append(Issue(svc, "critical", "rootfolder",
                                 f"Root folder inaccessible: {path}",
                                 "Check mount and permissions", fixable=False,
                                 fix_action="check_mount"))
            elif free < 10 * (1024**3):  # < 10 GB
                free_gb = round(free / (1024**3), 1)
                out.append(Issue(svc, "warning", "rootfolder",
                                 f"Root folder low space: {path} ({free_gb} GB free)",
                                 "Clean up old downloads or expand storage", fixable=False))
        return out

    # ── Remote path mapping validation ───────────────────────────────────────

    def _check_remote_path_mappings(self, connector, svc: str) -> list[Issue]:
        v = connector._api_prefix()
        try:
            r = connector.session.get(
                f"{connector.base_url}/api/{v}/remotepathmapping", timeout=8)
            r.raise_for_status()
            mappings = r.json()
        except Exception:
            return []
        out = []
        # Validate each mapping: remotePath must not look like a local path
        for m in mappings:
            remote = m.get("remotePath", "")
            local  = m.get("localPath",  "")
            host   = m.get("host",       "")
            # Warn if remote path looks wrong (e.g. same as local)
            if remote.startswith("/download") or remote == local:
                out.append(Issue(svc, "warning", "path",
                                 f"Suspicious remote path mapping: {remote} → {local}",
                                 f"Host: {host}. Remote should be the seedbox path, "
                                 "local should be the NAS mount path.",
                                 fixable=False, fix_action="fix_path_mapping"))
        return out

    # ── QNAP storage ──────────────────────────────────────────────────────────

    def _check_qnap_storage(self) -> list[Issue]:
        out = []
        try:
            s = self._qnap.get_storage_stats()
            if s.get("status") != "connected":
                out.append(Issue("qnap", "warning", "disk",
                                 f"Storage check failed: {s.get('status', 'unknown')}",
                                 fixable=False))
                return out
            pct  = s.get("used_pct", 0)
            free = s.get("free_gb", 0)
            if pct >= 92:
                out.append(Issue("qnap", "critical", "disk",
                                 f"QNAP disk critically full: {pct}% used ({free} GB free)",
                                 "Immediately remove completed downloads", fixable=False))
            elif pct >= 82:
                out.append(Issue("qnap", "warning", "disk",
                                 f"QNAP disk usage high: {pct}% used ({free} GB free)",
                                 "Consider cleaning up soon", fixable=False))
        except Exception as exc:
            out.append(Issue("qnap", "warning", "disk",
                             f"Storage check error: {str(exc)[:80]}", fixable=False))
        return out

    # ── rclone health ─────────────────────────────────────────────────────────

    def _check_rclone(self) -> list[Issue]:
        out = []
        try:
            r = self._qnap.get_rclone_status()
            if r.get("status") not in ("connected", "ok"):
                return out  # SSH not available, skip
            running = r.get("rclone_running", False)
            ago     = r.get("last_sync_ago_min")
            if ago is None and not running:
                out.append(Issue("rclone", "warning", "rclone",
                                 "rclone: no sync log found and not running",
                                 "Sync may never have run or log rotated", fixable=True,
                                 fix_action="force_rclone_sync"))
            elif ago is not None and ago > 60 and not running:
                out.append(Issue("rclone", "critical", "rclone",
                                 f"rclone hasn't synced in {ago} min",
                                 "Files stuck on seedbox — sync stopped", fixable=True,
                                 fix_action="force_rclone_sync"))
            elif ago is not None and ago > 30 and not running:
                out.append(Issue("rclone", "warning", "rclone",
                                 f"rclone sync is {ago} min old",
                                 "May be falling behind", fixable=True,
                                 fix_action="force_rclone_sync"))
            pending = r.get("pending_files", 0)
            if pending > 500:
                out.append(Issue("rclone", "warning", "rclone",
                                 f"Large download backlog: {pending} files in /share/download",
                                 "Verify rclone is processing files", fixable=False))
        except Exception as exc:
            out.append(Issue("rclone", "info", "rclone",
                             f"rclone check error: {str(exc)[:80]}", fixable=False))
        return out
