"""Backup module — manual Restic backup trigger + last-status read.

Per Block 2.5 D5: manual backup is Tier 3 (sensitive — handles
credentialed, externally-visible side effects). The control-plane
itself never holds the Restic credentials; it dispatches a trigger
file to the host launchd watcher which invokes
`/usr/local/bin/iap-backup-trigger.sh`.

Routes:
  GET  /api/backups/last      T1   read last status JSON
  POST /api/backups/run       T3   dispatch a manual backup
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .. import audit_log, triggers
from ..auth import Identity, require_tier1, require_tier3
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

# Status file written by the host trigger script. Mounted into the
# container via /var/run/iap (same volume as triggers, the host script
# writes the status next to its results).
_STATUS_PATH = Path(settings.trigger_dir) / "backup-status.json"


def _record(action: str, tier: int, ident: Identity, outcome: str, **detail) -> None:
    actions_total.labels(tier=str(tier), action=action, outcome=outcome).inc()
    audit_log.emit(
        action=action,
        tier=tier,
        outcome=outcome,
        actor_ip=ident.client_ip,
        tier3_active=ident.tier3_active,
        detail=detail,
    )


@router.get("/last")
async def get_last(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    if not _STATUS_PATH.exists():
        _record("backups.last", 1, ident, "empty")
        return {"status": "no_data", "reason": "no backup has been triggered yet"}
    try:
        data = json.loads(_STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        _record("backups.last", 1, ident, "fail", error=str(e))
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "backup status unreadable"
        )
    _record("backups.last", 1, ident, "success")
    return data


@router.post("/run")
async def run_backup(
    request: Request, ident: Identity = Depends(require_tier3)
) -> dict[str, Any]:
    """Dispatch a manual Restic backup. T3 — operator must be in the
    Tier 3 sliding-window (re-auth via /auth/unlock)."""
    try:
        result = await triggers.dispatch(
            "backup-trigger",
            params={},
            timeout_s=900.0,
            poll_interval_s=1.0,
        )
    except triggers.TriggerTimeout as e:
        _record("backups.run", 3, ident, "timeout", error=str(e))
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "backup timed out")
    except triggers.TriggerRejected as e:
        _record("backups.run", 3, ident, "rejected", error=str(e))
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except triggers.TriggerError as e:
        _record("backups.run", 3, ident, "fail", error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

    exit_code = result.get("exit_code", -1)
    outcome = "success" if exit_code == 0 else "fail"
    _record("backups.run", 3, ident, outcome, exit_code=exit_code)
    return result
