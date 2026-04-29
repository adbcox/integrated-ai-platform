"""Service registry module — reads from CMDB (NetBox or YAML).

Block 4.C C5.2c — staged toggle pattern. The module reads through
`scripts.cmdb_source.load_services()` which dispatches on the
$CMDB_SOURCE env var:

    CMDB_SOURCE=yaml   → /app/service-registry.yaml (default)
    CMDB_SOURCE=netbox → http://netbox:8080 (in-cluster NetBox)

Both backends produce byte-identical projections of the three
consumed fields below. See scripts/cmdb-equivalence.sh for the
contract. The default remains YAML during the C5.2 transition;
flip to netbox after C6 closes the regression probe.

Routes (all T1):
  GET /api/registry/services       — full list (id/name/category/host/container/port/depends_on)
  GET /api/registry/categories     — services grouped by category
  GET /api/registry/health         — health summary (GET probes against health_url)
"""
from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from .. import audit_log
from ..auth import Identity, require_tier1
from ..config import settings
from ..metrics import actions_total

# Make the shared loader importable. The Dockerfile copies
# scripts/cmdb_source.py to /app/cmdb_source.py — import it via the
# image-relative path. (Cannot live under app/ because it is also
# consumed as a host-side CLI script and by topology-api.)
sys.path.insert(0, "/app")
import cmdb_source  # noqa: E402

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
    """Load the service list and a metadata dict.

    YAML mode returns the registry's metadata block verbatim. NetBox
    mode synthesizes a minimal metadata stub (NetBox has no equivalent
    section). Endpoints that don't read metadata are unaffected.
    """
    src = (os.environ.get("CMDB_SOURCE") or settings.cmdb_source or "yaml").lower()
    if src == "yaml":
        # Pre-set the loader's path env so it reads the bind-mounted
        # registry instead of the in-repo default.
        os.environ["CMDB_REGISTRY"] = settings.service_registry_path
    elif src == "netbox":
        # cmdb_source reads NETBOX_URL / NETBOX_API_TOKEN /
        # NETBOX_CREDENTIALS_FILE itself.
        pass
    else:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"unknown CMDB_SOURCE={src!r} (expected yaml|netbox)",
        )
    try:
        services = cmdb_source.load_services()
    except FileNotFoundError:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "registry not mounted"
        )
    except SystemExit as e:
        # cmdb_source raises SystemExit on backend failures (token
        # missing, NetBox unreachable, YAML parse error).
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"cmdb load error: {e}"
        )

    # Sort by id and depends_on so the response shape is byte-stable
    # regardless of source iteration order (NetBox returns services in
    # a different order than registry YAML). Also normalize empty
    # strings to "" so the YAML→NetBox JSON round-trip is identical:
    # YAML preserves explicit nulls (container/host), NetBox drops
    # empties; normalize both into "" here.
    services = sorted(services, key=lambda s: s.get("id") or "")
    for s in services:
        s["depends_on"] = sorted(s.get("depends_on", []) or [])

    # Metadata is registry-YAML-only. Re-read just that block so the
    # services endpoint preserves its existing response shape.
    metadata: dict[str, Any] = {}
    if src == "yaml":
        try:
            import yaml
            p = Path(settings.service_registry_path)
            if p.exists():
                raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                metadata = raw.get("metadata", {}) or {}
        except Exception:  # parse errors already surfaced above via cmdb_source
            metadata = {}
    return {"metadata": metadata, "services": services}


@router.get("/services")
async def services(
    request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    data = _load()
    items = data.get("services", []) or []
    proj = []
    for s in items:
        # Normalize empties so YAML and NetBox sources project to the
        # same JSON shape. YAML preserves `container: null` keys; the
        # NetBox loader drops empty fields. Coerce both to "" / [].
        proj.append(
            {
                "id": s.get("id"),
                "name": s.get("name") or "",
                "category": s.get("category") or "",
                "host": s.get("host") or "",
                "container": s.get("container") or "",
                "port": s.get("port"),
                "depends_on": s.get("depends_on") or [],
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
        cat = s.get("category") or "uncategorized"
        grouped[cat].append(s.get("id"))
    # Sort so YAML and NetBox sources serialize identically.
    out = {k: sorted(v) for k, v in sorted(grouped.items())}
    _record("registry.categories", ident, "success", categories=len(out))
    return {"categories": out}


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
