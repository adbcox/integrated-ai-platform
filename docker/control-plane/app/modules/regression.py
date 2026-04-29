"""Regression probe module — dispatches the H1 regression probe.

Tier 3 because the probe touches Vault, the docker socket, etc., and
running it carries side-effects (it queries every health endpoint,
which can perturb stateful services). The container does not have
those capabilities; the host launchd watcher runs the probe.

Routes:
  POST /api/regression/run    T3   {gate_id: "block-2.5-gate-final"}
  GET  /api/regression/last   T1
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from .. import audit_log, triggers
from ..auth import Identity, require_tier1, require_tier3
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

_LAST_PATH = Path(settings.trigger_dir) / "regression-last.json"


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


class RunRequest(BaseModel):
    gate_id: str = "ad-hoc"


@router.post("/run")
async def run(
    payload: RunRequest,
    request: Request,
    ident: Identity = Depends(require_tier3),
) -> dict[str, Any]:
    if "/" in payload.gate_id or ".." in payload.gate_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid gate_id")
    try:
        result = await triggers.dispatch(
            "regression-probe",
            params={"gate_id": payload.gate_id},
            timeout_s=300.0,
            poll_interval_s=1.0,
        )
    except triggers.TriggerTimeout:
        _record("regression.run", 3, ident, "timeout", gate_id=payload.gate_id)
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "regression timed out")
    except triggers.TriggerRejected as e:
        _record("regression.run", 3, ident, "rejected", gate_id=payload.gate_id,
                reason=str(e))
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except triggers.TriggerError as e:
        _record("regression.run", 3, ident, "fail", gate_id=payload.gate_id,
                error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))

    summary = {
        "gate_id": payload.gate_id,
        "exit_code": result.get("exit_code", -1),
        "pass": result.get("pass_count", 0),
        "fail": result.get("fail_count", 0),
        "warn": result.get("warn_count", 0),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "log_tail_b64": result.get("log_tail_b64"),
    }
    outcome = "success" if summary["fail"] == 0 and summary["exit_code"] == 0 else "fail"
    _record("regression.run", 3, ident, outcome,
            gate_id=payload.gate_id, **{k: summary[k] for k in ("pass", "fail", "warn")})
    return summary


@router.get("/last")
async def last(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    if not _LAST_PATH.exists():
        _record("regression.last", 1, ident, "empty")
        return {"status": "no_data"}
    try:
        data = json.loads(_LAST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        _record("regression.last", 1, ident, "fail", error=str(e))
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "regression status unreadable"
        )
    _record("regression.last", 1, ident, "success")
    return data
