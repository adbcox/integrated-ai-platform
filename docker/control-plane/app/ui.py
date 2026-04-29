"""HTMX UI router — renders Jinja templates and HTMX partials.

The UI talks to the same FastAPI app's HTTP API for all state-mutating
operations (POST /api/...). Read-only listings are rendered server-side
to keep the JS minimal.

Routes:
  GET /                       index
  GET /ui/containers          full page
  GET /ui/services            full page
  GET /ui/registry            full page
  GET /ui/backups             full page
  GET /ui/credentials         full page
  GET /ui/audit               full page
  GET /ui/regression          full page

  GET /ui/_auth-banner        partial (auto-refreshing in base.html)
  GET /ui/_partials/*         partial fragments
  GET /ui/_summary/*          dashboard tiles
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import __version__
from .auth import Identity, get_identity, require_tier1, tier3_remaining_seconds
from .config import settings

log = logging.getLogger(__name__)
router = APIRouter()

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

# Internal HTTP client — talks to our own FastAPI on localhost. We
# share the same process, so this hops through localhost rather than
# importing the route handlers (avoids re-running auth dependencies
# in a different request context).
_INTERNAL_BASE = f"http://127.0.0.1:{settings.listen_port}"
_TIMEOUT = httpx.Timeout(connect=1.0, read=5.0, write=2.0, pool=2.0)


async def _internal_get(
    request: Request, path: str, params: dict | None = None
) -> httpx.Response:
    """Forward the caller's tailnet identity headers so the inner
    FastAPI request preserves the client IP."""
    headers = {}
    xff = request.headers.get("x-forwarded-for")
    if xff:
        headers["X-Forwarded-For"] = xff
    elif request.client:
        headers["X-Forwarded-For"] = request.client.host
    async with httpx.AsyncClient(base_url=_INTERNAL_BASE, timeout=_TIMEOUT) as c:
        return await c.get(path, params=params or {}, headers=headers)


def _ctx(request: Request, **extra) -> dict[str, Any]:
    ident = get_identity(request)
    base = {
        "request": request,
        "version": __version__,
        "ident": ident,
        "tier3_remaining": tier3_remaining_seconds(request),
    }
    base.update(extra)
    return base


# ── Full pages ────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def index(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "index.html", _ctx(request, title="Control Plane")
    )


@router.get("/ui/containers", response_class=HTMLResponse)
async def page_containers(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "containers.html", _ctx(request, title="Containers")
    )


@router.get("/ui/services", response_class=HTMLResponse)
async def page_services(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "services.html", _ctx(request, title="Services")
    )


@router.get("/ui/registry", response_class=HTMLResponse)
async def page_registry(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "registry.html", _ctx(request, title="Registry")
    )


@router.get("/ui/backups", response_class=HTMLResponse)
async def page_backups(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "backups.html", _ctx(request, title="Backups")
    )


@router.get("/ui/credentials", response_class=HTMLResponse)
async def page_credentials(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "credentials.html", _ctx(request, title="Credentials")
    )


@router.get("/ui/audit", response_class=HTMLResponse)
async def page_audit(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "audit.html", _ctx(request, title="Audit")
    )


@router.get("/ui/regression", response_class=HTMLResponse)
async def page_regression(request: Request, _: Identity = Depends(require_tier1)):
    return templates.TemplateResponse(
        "regression.html", _ctx(request, title="Regression")
    )


# ── Partials ──────────────────────────────────────────────────────────
@router.get("/ui/_auth-banner", response_class=HTMLResponse)
async def auth_banner(request: Request):
    return templates.TemplateResponse("_auth_banner.html", _ctx(request))


@router.get("/ui/_partials/containers", response_class=HTMLResponse)
async def part_containers(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/containers")
    items = r.json() if r.status_code == 200 else []
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="containers", containers=items)
    )


@router.get("/ui/_partials/sonarr-queue", response_class=HTMLResponse)
async def part_sonarr(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/services/sonarr/queue")
    data = r.json() if r.status_code == 200 else {"queue": []}
    return templates.TemplateResponse(
        "_partials.html",
        _ctx(request, kind="queue", service="sonarr", queue=data.get("queue", [])),
    )


@router.get("/ui/_partials/radarr-queue", response_class=HTMLResponse)
async def part_radarr(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/services/radarr/queue")
    data = r.json() if r.status_code == 200 else {"queue": []}
    return templates.TemplateResponse(
        "_partials.html",
        _ctx(request, kind="queue", service="radarr", queue=data.get("queue", [])),
    )


@router.get("/ui/_partials/prowlarr-indexers", response_class=HTMLResponse)
async def part_prowlarr(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/services/prowlarr/indexers")
    data = r.json() if r.status_code == 200 else {"indexers": []}
    return templates.TemplateResponse(
        "_partials.html",
        _ctx(request, kind="indexers", indexers=data.get("indexers", [])),
    )


@router.get("/ui/_partials/registry", response_class=HTMLResponse)
async def part_registry(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/registry/services")
    data = r.json() if r.status_code == 200 else {"services": []}
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="registry", services=data.get("services", []))
    )


@router.get("/ui/_partials/credentials", response_class=HTMLResponse)
async def part_credentials(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/credentials/paths")
    data = r.json() if r.status_code == 200 else {"namespaces": {}}
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="credentials", namespaces=data.get("namespaces", {}))
    )


@router.get("/ui/_partials/audit", response_class=HTMLResponse)
async def part_audit(
    request: Request,
    source: str = "actions",
    q: str | None = None,
    tail: int = 100,
    _: Identity = Depends(require_tier1),
):
    if source not in ("actions", "vault", "caddy"):
        source = "actions"
    params: dict[str, Any] = {"tail": str(tail)}
    if q:
        params["q"] = q
    r = await _internal_get(request, f"/api/audit/{source}", params=params)
    data = r.json() if r.status_code == 200 else {"events": []}
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="audit", events=data.get("events", []))
    )


@router.get("/ui/_partials/last-backup", response_class=HTMLResponse)
async def part_last_backup(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/backups/last")
    data = r.json() if r.status_code == 200 else None
    if data and data.get("status") == "no_data":
        data = None
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="last-backup", data=data)
    )


# ── Dashboard tiles ───────────────────────────────────────────────────
@router.get("/ui/_summary/containers", response_class=HTMLResponse)
async def sum_containers(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/containers")
    items = r.json() if r.status_code == 200 else []
    counts = Counter(c.get("state") for c in items)
    return templates.TemplateResponse(
        "_partials.html",
        _ctx(
            request,
            kind="summary-containers",
            counts={
                "total": sum(counts.values()),
                "running": counts.get("running", 0),
                "exited": counts.get("exited", 0),
                "restarting": counts.get("restarting", 0),
            },
        ),
    )


@router.get("/ui/_summary/registry-health", response_class=HTMLResponse)
async def sum_registry_health(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/registry/health")
    data = r.json() if r.status_code == 200 else {"total": 0, "ok": 0}
    return templates.TemplateResponse(
        "_partials.html",
        _ctx(request, kind="summary-registry-health", total=data.get("total", 0), ok=data.get("ok", 0)),
    )


@router.get("/ui/_summary/last-backup", response_class=HTMLResponse)
async def sum_last_backup(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/backups/last")
    data = r.json() if r.status_code == 200 else None
    if data and data.get("status") == "no_data":
        data = None
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="last-backup", data=data)
    )


@router.get("/ui/_summary/recent-actions", response_class=HTMLResponse)
async def sum_recent(request: Request, _: Identity = Depends(require_tier1)):
    r = await _internal_get(request, "/api/audit/actions", params={"tail": "10"})
    data = r.json() if r.status_code == 200 else {"events": []}
    return templates.TemplateResponse(
        "_partials.html", _ctx(request, kind="summary-recent", events=data.get("events", []))
    )
