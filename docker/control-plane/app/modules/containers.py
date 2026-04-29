"""Container actions module.

Talks to docker-socket-proxy-control:2375 (linuxserver/socket-proxy
hardened with allowlist CONTAINERS=1, INFO=1, POST=1, EXEC=1, all
others off). The proxy enforces API-method allowlist; this module
adds operation-level scoping by tier.

Tiers (per Block 2.5 audit D5):
  T1 read   list, inspect, logs
  T2 write  start, stop, restart
  T3 exec   gated separately (Phase 3 deferred — not in initial cut;
            requires per-container `com.iap.exec.allowed` label parsing)
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from .. import audit_log
from ..auth import Identity, require_tier1, require_tier2
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

# socket-proxy speaks HTTP on tcp://<host>:2375; httpx does not need
# the docker UDS adapter. Path is the standard Docker Engine API.
_BASE = settings.docker_host.replace("tcp://", "http://")
_TIMEOUT = httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=2.0)


async def _engine_get(path: str, params: dict | None = None) -> httpx.Response:
    async with httpx.AsyncClient(base_url=_BASE, timeout=_TIMEOUT) as c:
        return await c.get(path, params=params or {})


async def _engine_post(path: str, params: dict | None = None) -> httpx.Response:
    async with httpx.AsyncClient(base_url=_BASE, timeout=_TIMEOUT) as c:
        return await c.post(path, params=params or {})


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


# ── T1 read ───────────────────────────────────────────────────────────
@router.get("")
async def list_containers(
    request: Request,
    all: bool = Query(default=True),
    ident: Identity = Depends(require_tier1),
) -> list[dict[str, Any]]:
    r = await _engine_get("/containers/json", params={"all": str(all).lower()})
    if r.status_code != 200:
        _record("containers.list", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "docker proxy error")
    items = r.json()
    out: list[dict[str, Any]] = []
    for c in items:
        out.append(
            {
                "id": c.get("Id", "")[:12],
                "names": [n.lstrip("/") for n in c.get("Names", [])],
                "image": c.get("Image", ""),
                "state": c.get("State", ""),
                "status": c.get("Status", ""),
                "labels": {
                    k: v
                    for k, v in (c.get("Labels") or {}).items()
                    if k.startswith("com.iap.")
                },
            }
        )
    _record("containers.list", 1, ident, "success", count=len(out))
    return out


@router.get("/{cid}/inspect")
async def inspect_container(
    cid: str, request: Request, ident: Identity = Depends(require_tier1)
) -> dict[str, Any]:
    r = await _engine_get(f"/containers/{cid}/json")
    if r.status_code == 404:
        _record("containers.inspect", 1, ident, "not_found", cid=cid)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "container not found")
    if r.status_code != 200:
        _record("containers.inspect", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "docker proxy error")
    raw = r.json()
    _record("containers.inspect", 1, ident, "success", cid=cid)
    state = raw.get("State", {})
    return {
        "id": raw.get("Id", "")[:12],
        "name": raw.get("Name", "").lstrip("/"),
        "image": (raw.get("Config") or {}).get("Image", ""),
        "state": {
            "status": state.get("Status"),
            "running": state.get("Running"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "restart_count": raw.get("RestartCount"),
            "health": (state.get("Health") or {}).get("Status"),
        },
        "labels": {
            k: v
            for k, v in ((raw.get("Config") or {}).get("Labels") or {}).items()
            if k.startswith("com.iap.")
        },
        "networks": list((raw.get("NetworkSettings") or {}).get("Networks", {}).keys()),
    }


@router.get("/{cid}/logs")
async def container_logs(
    cid: str,
    request: Request,
    tail: int = Query(default=200, ge=1, le=2000),
    ident: Identity = Depends(require_tier1),
) -> dict[str, Any]:
    """Return the last `tail` lines (stdout+stderr). Docker engine
    returns logs in a multiplexed framed stream; we do a best-effort
    decode since the socket-proxy still returns the framed payload.
    """
    r = await _engine_get(
        f"/containers/{cid}/logs",
        params={
            "stdout": "true",
            "stderr": "true",
            "tail": str(tail),
            "timestamps": "true",
        },
    )
    if r.status_code == 404:
        _record("containers.logs", 1, ident, "not_found", cid=cid)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "container not found")
    if r.status_code != 200:
        _record("containers.logs", 1, ident, "fail", code=r.status_code)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "docker proxy error")

    raw = r.content
    decoded = _demux_log(raw)
    _record("containers.logs", 1, ident, "success", cid=cid, bytes=len(raw))
    return {"cid": cid, "lines": decoded.splitlines()}


def _demux_log(buf: bytes) -> str:
    """Best-effort demux of Docker's 8-byte-header framed stream. If
    the buffer doesn't look framed (e.g. tty-mode container), fall
    through and decode as plain UTF-8 with replacement.
    """
    if len(buf) < 8:
        return buf.decode("utf-8", errors="replace")
    # Heuristic: framed headers have stream byte ∈ {1,2}, three reserved 0s
    if buf[0] in (1, 2) and buf[1] == 0 and buf[2] == 0 and buf[3] == 0:
        out = bytearray()
        i = 0
        n = len(buf)
        while i + 8 <= n:
            length = int.from_bytes(buf[i + 4 : i + 8], "big")
            i += 8
            if i + length > n:
                break
            out.extend(buf[i : i + length])
            i += length
        return out.decode("utf-8", errors="replace")
    return buf.decode("utf-8", errors="replace")


# ── T2 write ──────────────────────────────────────────────────────────
@router.post("/{cid}/restart")
async def restart_container(
    cid: str, request: Request, ident: Identity = Depends(require_tier2)
) -> dict[str, Any]:
    r = await _engine_post(f"/containers/{cid}/restart")
    return _post_result("containers.restart", cid, r, ident)


@router.post("/{cid}/stop")
async def stop_container(
    cid: str, request: Request, ident: Identity = Depends(require_tier2)
) -> dict[str, Any]:
    r = await _engine_post(f"/containers/{cid}/stop")
    return _post_result("containers.stop", cid, r, ident)


@router.post("/{cid}/start")
async def start_container(
    cid: str, request: Request, ident: Identity = Depends(require_tier2)
) -> dict[str, Any]:
    r = await _engine_post(f"/containers/{cid}/start")
    return _post_result("containers.start", cid, r, ident)


def _post_result(
    action: str, cid: str, r: httpx.Response, ident: Identity
) -> dict[str, Any]:
    if r.status_code in (204, 304):
        _record(action, 2, ident, "success", cid=cid, code=r.status_code)
        return {"cid": cid, "status": "ok", "code": r.status_code}
    if r.status_code == 404:
        _record(action, 2, ident, "not_found", cid=cid)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "container not found")
    _record(action, 2, ident, "fail", cid=cid, code=r.status_code)
    raise HTTPException(status.HTTP_502_BAD_GATEWAY, "docker proxy error")
