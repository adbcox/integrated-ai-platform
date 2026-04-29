"""Configuration drift / summary module.

The control-plane container is intentionally minimal — it does not
mount the full repo. So we expose:
  - File summaries (size, mtime) for the configs we DO see (registry,
    log files we mount RO).
  - Vault policy enumeration (read-only) via Vault sys API.

Operators use this to spot last-modified drift; deeper diffs are a
host-side concern.

Routes (all T1):
  GET /api/config/summary
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request

from .. import audit_log
from ..auth import Identity, require_tier1
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()


def _record(action: str, ident: Identity, outcome: str, **detail) -> None:
    actions_total.labels(tier="1", action=action, outcome=outcome).inc()
    audit_log.emit(
        action=action,
        tier=1,
        outcome=outcome,
        actor_ip=ident.client_ip,
        tier3_active=ident.tier3_active,
        detail=detail,
    )


def _stat(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"path": path, "exists": False}
    st = p.stat()
    return {
        "path": path,
        "exists": True,
        "size": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "mode": oct(st.st_mode & 0o777),
    }


@router.get("/summary")
async def summary(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    files = [
        settings.service_registry_path,
        settings.audit_log_path,
        settings.caddy_access_log_path,
        settings.actions_log_path,
        settings.vault_token_path,
    ]
    out = [_stat(f) for f in files]
    _record("config.summary", ident, "success", count=len(out))
    return {"files": out}
