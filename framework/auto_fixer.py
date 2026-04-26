"""Auto-fix engine for media pipeline issues."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

if TYPE_CHECKING:
    from framework.health_checker import Issue


class FixResult:
    def __init__(self, ok: bool, action: str, detail: str, error: str = "") -> None:
        self.ok     = ok
        self.action = action
        self.detail = detail
        self.error  = error

    def as_dict(self) -> dict:
        return {"ok": self.ok, "action": self.action,
                "detail": self.detail, "error": self.error}


class AutoFixer:
    """Apply fixes for issues that can be resolved programmatically."""

    def __init__(self) -> None:
        from connectors.arr_stack import ArrStackConnector
        from connectors.qnap import QNAPConnector

        self._sonarr = ArrStackConnector(
            "sonarr",   os.environ.get("SONARR_URL",   "http://192.168.10.201:8989"),
                        os.environ.get("SONARR_API_KEY", ""))
        self._radarr = ArrStackConnector(
            "radarr",   os.environ.get("RADARR_URL",   "http://192.168.10.201:7878"),
                        os.environ.get("RADARR_API_KEY", ""))
        self._qnap = QNAPConnector(
            os.environ.get("QNAP_URL",  "http://192.168.10.201"),
            os.environ.get("QNAP_USER", "admin"),
            os.environ.get("QNAP_PASS", ""))

    # ── Main dispatch ─────────────────────────────────────────────────────────

    def apply(self, issue: "Issue") -> FixResult | None:
        """Apply the fix for a fixable issue. Returns None if not fixable."""
        if not issue.fixable:
            return None
        dispatch = {
            "remove_and_requeue": self._fix_remove_and_requeue,
            "force_rclone_sync":  self._fix_force_rclone,
            "rss_sync":           self._fix_rss_sync,
        }
        fn = dispatch.get(issue.fix_action)
        if fn is None:
            return FixResult(False, issue.fix_action, "No handler for this fix type")
        try:
            return fn(issue)
        except Exception as exc:
            return FixResult(False, issue.fix_action, issue.message, str(exc))

    def apply_all(self, issues: list) -> list[FixResult]:
        """Apply fixes for all fixable issues, deduplicating by action+data."""
        seen:    set[str] = set()
        results: list[FixResult] = []
        for issue in issues:
            if not issue.fixable:
                continue
            key = f"{issue.fix_action}:{issue.fix_data}"
            if key in seen:
                continue
            seen.add(key)
            result = self.apply(issue)
            if result:
                results.append(result)
                time.sleep(0.5)  # brief pause between fixes
        return results

    # ── Fix implementations ───────────────────────────────────────────────────

    def _fix_remove_and_requeue(self, issue: "Issue") -> FixResult:
        """Remove a failed queue item and trigger a search for it."""
        svc      = issue.fix_data.get("service", issue.service)
        queue_id = issue.fix_data.get("queue_id")
        if not queue_id:
            return FixResult(False, "remove_and_requeue", "No queue_id in fix_data")

        connector = self._sonarr if svc == "sonarr" else self._radarr
        removed = connector.remove_from_queue(queue_id, blacklist=True)
        if not removed:
            return FixResult(False, "remove_and_requeue",
                             f"Failed to remove queue item {queue_id} from {svc}")

        # Trigger search for what was removed
        time.sleep(1)
        searched = connector.search_missing_all()
        detail = f"Removed queue item {queue_id} from {svc}"
        if searched:
            detail += " and triggered search for missing content"
        return FixResult(True, "remove_and_requeue", detail)

    def _fix_force_rclone(self, issue: "Issue") -> FixResult:
        """Trigger rclone sync on QNAP via SSH."""
        result = self._qnap.force_rclone_sync()
        ok     = result.get("ok", False)
        msg    = result.get("message", "")
        return FixResult(ok, "force_rclone_sync", msg or "Sync triggered",
                         "" if ok else msg)

    def _fix_rss_sync(self, issue: "Issue") -> FixResult:
        """Trigger RSS sync on Sonarr and Radarr."""
        svc = issue.service
        connector = self._sonarr if svc == "sonarr" else self._radarr
        v   = connector._api_prefix()
        try:
            r = connector.session.post(
                f"{connector.base_url}/api/{v}/command",
                json={"name": "RssSync"}, timeout=10)
            ok = r.status_code in (200, 201, 202)
            return FixResult(ok, "rss_sync",
                             f"RSS sync triggered on {svc}" if ok else "Failed to trigger RSS sync")
        except Exception as exc:
            return FixResult(False, "rss_sync", f"RSS sync error: {svc}", str(exc))

    # ── Targeted fixes (called from API endpoints) ────────────────────────────

    def trigger_rss_sync_all(self) -> dict[str, bool]:
        """Trigger RSS sync on both Sonarr and Radarr. Returns {service: ok}."""
        results = {}
        for svc, connector in [("sonarr", self._sonarr), ("radarr", self._radarr)]:
            v = connector._api_prefix()
            try:
                r = connector.session.post(
                    f"{connector.base_url}/api/{v}/command",
                    json={"name": "RssSync"}, timeout=10)
                results[svc] = r.status_code in (200, 201, 202)
            except Exception:
                results[svc] = False
        return results

    def trigger_missing_search_all(self) -> dict[str, bool]:
        """Trigger search for all missing monitored content."""
        return {
            "sonarr": self._sonarr.search_missing_all(),
            "radarr": self._radarr.search_missing_all(),
        }

    def get_arr_config_summary(self) -> dict:
        """Return a structured summary of *arr configuration for health display."""
        summary = {}
        for svc, connector in [("sonarr", self._sonarr), ("radarr", self._radarr)]:
            v = connector._api_prefix()
            entry: dict = {"service": svc, "reachable": False}
            try:
                if not connector.health_check():
                    summary[svc] = entry
                    continue
                entry["reachable"] = True

                r = connector.session.get(f"{connector.base_url}/api/{v}/rootfolder", timeout=8)
                entry["root_folders"] = [
                    {"path": f.get("path"), "accessible": f.get("accessible"),
                     "free_gb": round(f.get("freeSpace", 0) / (1024**3), 1)}
                    for f in r.json()
                ] if r.ok else []

                r = connector.session.get(f"{connector.base_url}/api/{v}/remotepathmapping", timeout=8)
                entry["path_mappings"] = [
                    {"host": m.get("host"), "remote": m.get("remotePath"), "local": m.get("localPath")}
                    for m in r.json()
                ] if r.ok else []

                r = connector.session.get(f"{connector.base_url}/api/{v}/downloadclient", timeout=8)
                if r.ok:
                    clients = r.json()
                    if isinstance(clients, list):
                        entry["download_clients"] = [
                            {"name": c.get("name"), "protocol": c.get("protocol"),
                             "enable": c.get("enable", True)}
                            for c in clients
                        ]
                    else:
                        entry["download_clients"] = []

            except Exception as exc:
                entry["error"] = str(exc)[:80]
            summary[svc] = entry
        return summary
