"""Service-specific actions — Sonarr / Radarr / Prowlarr.

Sonarr/Radarr expose v3 API; Prowlarr exposes v1. Each requires
`X-Api-Key` (rendered into env by the Vault Agent sidecar). We keep
endpoints narrow: queue, indexers, system health. Removing/retrying
queue items is T2.

Routes:
  GET    /api/services/{name}/health        T1   system status
  GET    /api/services/sonarr/queue         T1
  GET    /api/services/radarr/queue         T1
  GET    /api/services/prowlarr/indexers    T1
  POST   /api/services/{name}/queue/{id}/retry  T2
  DELETE /api/services/{name}/queue/{id}    T2
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from .. import audit_log
from ..auth import Identity, require_tier1, require_tier2
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

_TIMEOUT = httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=2.0)


def _service_url(name: str) -> tuple[str, str, str]:
    """Returns (base_url, api_version, api_key) for a service name."""
    if name == "sonarr":
        return settings.sonarr_url, "v3", settings.sonarr_api_key
    if name == "radarr":
        return settings.radarr_url, "v3", settings.radarr_api_key
    if name == "prowlarr":
        return settings.prowlarr_url, "v1", settings.prowlarr_api_key
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"unknown service {name!r}")


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


async def _api(
    name: str, method: str, path: str, params: dict | None = None
) -> httpx.Response:
    base, ver, key = _service_url(name)
    if not key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"{name}: api key not rendered"
        )
    async with httpx.AsyncClient(base_url=base, timeout=_TIMEOUT) as c:
        return await c.request(
            method,
            f"/api/{ver}{path}",
            params=params or {},
            headers={"X-Api-Key": key},
        )


@router.get("/{name}/health")
async def system_health(
    name: str, request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    r = await _api(name, "GET", "/health")
    if r.status_code != 200:
        _record(f"{name}.health", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{name} health unreachable")
    items = r.json()
    _record(f"{name}.health", 1, ident, "success", count=len(items))
    return {"service": name, "issues": items}


@router.get("/sonarr/queue")
async def sonarr_queue(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    return await _queue("sonarr", request, ident)


@router.get("/radarr/queue")
async def radarr_queue(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    return await _queue("radarr", request, ident)


async def _queue(name: str, request: Request, ident: Identity) -> dict[str, Any]:
    r = await _api(
        name,
        "GET",
        "/queue",
        params={"pageSize": "100", "includeUnknownSeriesItems": "true"},
    )
    if r.status_code != 200:
        _record(f"{name}.queue", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{name} queue error")
    raw = r.json()
    items = raw.get("records", []) or raw if isinstance(raw, list) else raw.get("records", [])
    out = []
    for it in items or []:
        out.append(
            {
                "id": it.get("id"),
                "title": it.get("title")
                or (it.get("series") or {}).get("title")
                or (it.get("movie") or {}).get("title"),
                "status": it.get("status"),
                "tracked_status": it.get("trackedDownloadStatus"),
                "size_bytes": it.get("size"),
                "size_left_bytes": it.get("sizeleft"),
                "estimated_completion": it.get("estimatedCompletionTime"),
                "error_message": it.get("errorMessage"),
            }
        )
    _record(f"{name}.queue", 1, ident, "success", count=len(out))
    return {"service": name, "queue": out, "total": raw.get("totalRecords") if isinstance(raw, dict) else len(out)}


@router.get("/prowlarr/indexers")
async def prowlarr_indexers(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    r = await _api("prowlarr", "GET", "/indexer")
    if r.status_code != 200:
        _record("prowlarr.indexers", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "prowlarr indexers error")
    items = r.json()
    out = [
        {
            "id": it.get("id"),
            "name": it.get("name"),
            "enabled": it.get("enable"),
            "protocol": it.get("protocol"),
            "privacy": it.get("privacy"),
            "priority": it.get("priority"),
        }
        for it in items
    ]
    _record("prowlarr.indexers", 1, ident, "success", count=len(out))
    return {"service": "prowlarr", "indexers": out}


@router.post("/{name}/queue/{qid}/retry")
async def queue_retry(
    name: str,
    qid: int,
    request: Request,
    ident: Identity = Depends(require_tier2),
) -> dict[str, Any]:
    r = await _api(name, "POST", f"/queue/grab/{qid}")
    if r.status_code not in (200, 202):
        _record(f"{name}.queue.retry", 2, ident, "fail", qid=qid, code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{name} retry error")
    _record(f"{name}.queue.retry", 2, ident, "success", qid=qid)
    return {"service": name, "qid": qid, "status": "retried"}


@router.delete("/{name}/queue/{qid}")
async def queue_remove(
    name: str,
    qid: int,
    request: Request,
    ident: Identity = Depends(require_tier2),
    blocklist: bool = False,
) -> dict[str, Any]:
    r = await _api(
        name,
        "DELETE",
        f"/queue/{qid}",
        params={
            "removeFromClient": "true",
            "blocklist": str(blocklist).lower(),
        },
    )
    if r.status_code not in (200, 204):
        _record(f"{name}.queue.remove", 2, ident, "fail", qid=qid, code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{name} remove error")
    _record(f"{name}.queue.remove", 2, ident, "success", qid=qid, blocklist=blocklist)
    return {"service": name, "qid": qid, "status": "removed"}
