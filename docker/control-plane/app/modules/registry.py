"""Service registry module — parses service-registry.yaml.

Mounted RO at /app/service-registry.yaml. This is the canonical
machine-readable CMDB for the platform; the frontend uses it to
render the service grid and depends_on graph.

Routes (all T1):
  GET /api/registry/services       — full list
  GET /api/registry/categories     — services grouped by category
  GET /api/registry/health         — health summary (HEAD probes against health_url)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, status

from .. import audit_log
from ..auth import Identity, require_tier1
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

_TIMEOUT = httpx.Timeout(connect=1.0, read=3.0, write=2.0, pool=2.0)


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


def _load() -> dict[str, Any]:
    p = Path(settings.service_registry_path)
    if not p.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "registry not mounted"
        )
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"registry parse error: {e}"
        )


@router.get("/services")
async def services(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    data = _load()
    items = data.get("services", []) or []
    proj = []
    for s in items:
        proj.append(
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "category": s.get("category"),
                "host": s.get("host"),
                "container": s.get("container"),
                "port": s.get("port"),
                "depends_on": s.get("depends_on", []),
            }
        )
    _record("registry.services", ident, "success", count=len(proj))
    return {"metadata": data.get("metadata", {}), "services": proj}


@router.get("/categories")
async def categories(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    data = _load()
    grouped: dict[str, list[str]] = defaultdict(list)
    for s in data.get("services", []) or []:
        grouped[s.get("category", "uncategorized")].append(s.get("id"))
    _record("registry.categories", ident, "success", categories=len(grouped))
    return {"categories": dict(grouped)}


@router.get("/health")
async def health(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    """Best-effort health probe of every service that defines a
    health_url. Probes are bounded to ~3s each, parallel via
    asyncio.gather. We DO NOT chase 3xx redirects (would amplify
    timeout cost)."""
    import asyncio

    data = _load()
    items = data.get("services", []) or []

    async def probe(svc: dict) -> dict:
        url = svc.get("health_url")
        if not url:
            return {"id": svc.get("id"), "status": "no_url"}
        # Replace localhost in health_url with host.docker.internal so
        # we reach the host-bound port from inside the container.
        url = url.replace("http://localhost:", "http://host.docker.internal:")
        url = url.replace("https://localhost:", "https://host.docker.internal:")
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT, follow_redirects=False
            ) as c:
                r = await c.get(url)
            return {
                "id": svc.get("id"),
                "status": "ok" if 200 <= r.status_code < 400 else "degraded",
                "code": r.status_code,
            }
        except (httpx.HTTPError, OSError) as e:
            return {"id": svc.get("id"), "status": "unreachable", "error": type(e).__name__}

    results = await asyncio.gather(*(probe(s) for s in items))
    ok = sum(1 for r in results if r.get("status") == "ok")
    _record("registry.health", ident, "success",
            total=len(results), ok=ok)
    return {"total": len(results), "ok": ok, "results": results}
