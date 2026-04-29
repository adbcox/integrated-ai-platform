"""Credentials module — KV path enumeration + rotation dispatch.

Doctrine: NEVER return credential values. This module returns:
  - KV paths (via secret/metadata/<engine>/?list=true)
  - Per-secret metadata (versions, created_time)
  - Rotation history (filtered from the action audit log)

Rotation itself runs as Tier 3 via the trigger file → host launchd
path. The control-plane never holds the root token needed to mint
new secrets; that work is the host script's responsibility.

Routes:
  GET  /api/credentials/paths            T1
  GET  /api/credentials/{path:path}      T1   metadata only
  GET  /api/credentials/rotation-history T1
  POST /api/credentials/rotate           T3   {target: "arr/sonarr"}
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from .. import audit_log, triggers
from ..auth import Identity, require_tier1, require_tier3
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

_TIMEOUT = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=2.0)
# Top-level KV namespaces we expect the control-plane to enumerate.
# The control-plane policy (config/vault-policies/control-plane-policy.hcl)
# grants metadata list on these only.
_NAMESPACES = ("control-plane", "arr", "restic", "minio")


def _read_token() -> str:
    try:
        return Path(settings.vault_token_path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


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


async def _vault_list(client: httpx.AsyncClient, ns: str) -> list[str]:
    r = await client.request(
        "LIST",
        f"{settings.vault_addr}/v1/secret/metadata/{ns}",
        headers={"X-Vault-Token": _read_token()},
    )
    if r.status_code == 404:
        return []
    if r.status_code != 200:
        return []
    return list(r.json().get("data", {}).get("keys", []) or [])


@router.get("/paths")
async def list_paths(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    out: dict[str, list[str]] = {}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        for ns in _NAMESPACES:
            keys = await _vault_list(c, ns)
            out[ns] = [f"{ns}/{k.rstrip('/')}" for k in keys]
    total = sum(len(v) for v in out.values())
    _record("credentials.paths", 1, ident, "success", total=total)
    return {"namespaces": out, "total": total}


@router.get("/{path:path}")
async def get_metadata(
    path: str, request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    """Return metadata only (versions, created_time). Never returns
    the secret value."""
    if any(seg in ("..", "") for seg in path.split("/")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid path")
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(
            f"{settings.vault_addr}/v1/secret/metadata/{path}",
            headers={"X-Vault-Token": _read_token()},
        )
    if r.status_code == 403:
        _record("credentials.meta", 1, ident, "denied", path=path)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "denied by policy")
    if r.status_code == 404:
        _record("credentials.meta", 1, ident, "not_found", path=path)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such secret")
    if r.status_code != 200:
        _record("credentials.meta", 1, ident, "fail", path=path, code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "vault metadata error")
    data = r.json().get("data", {}) or {}
    _record("credentials.meta", 1, ident, "success", path=path)
    # Strip data, return only metadata fields
    return {
        "path": path,
        "current_version": data.get("current_version"),
        "created_time": data.get("created_time"),
        "updated_time": data.get("updated_time"),
        "versions_count": len(data.get("versions", {}) or {}),
        "max_versions": data.get("max_versions"),
    }


class RotateRequest(BaseModel):
    target: str  # e.g. "arr/sonarr"


@router.post("/rotate")
async def rotate(
    payload: RotateRequest,
    request: Request,
    ident: Identity = Depends(require_tier3),
) -> dict[str, Any]:
    if any(seg in ("..", "") for seg in payload.target.split("/")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid target")
    try:
        result = await triggers.dispatch(
            "credential-rotate",
            params={"target": payload.target},
            timeout_s=120.0,
            poll_interval_s=0.5,
        )
    except triggers.TriggerTimeout:
        _record("credentials.rotate", 3, ident, "timeout", target=payload.target)
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "rotation timed out")
    except triggers.TriggerRejected as e:
        _record("credentials.rotate", 3, ident, "rejected", target=payload.target,
                reason=str(e))
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except triggers.TriggerError as e:
        _record("credentials.rotate", 3, ident, "fail", target=payload.target,
                error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    exit_code = result.get("exit_code", -1)
    outcome = "success" if exit_code == 0 else "fail"
    # Hash-only verification: return hash digest if the rotation script
    # placed one in result.hash; never return the value itself.
    safe = {
        "target": payload.target,
        "exit_code": exit_code,
        "hash_prefix": result.get("hash_prefix"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
    }
    _record("credentials.rotate", 3, ident, outcome, target=payload.target,
            exit_code=exit_code)
    return safe
