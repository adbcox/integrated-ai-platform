"""FastAPI entrypoint for the operator control plane.

Phase 2: scaffolding only. Auth surfaces and module routers are
mounted but action implementations land in Phase 3 (P3.1–P3.8).

Routes mounted in Phase 2:
  GET  /healthz            — liveness
  GET  /metrics            — Prometheus
  POST /auth/unlock        — verify operator password, open Tier 3
  POST /auth/lock          — close Tier 3
  GET  /auth/status        — current identity + tier3 remaining

Module routers mounted with placeholder endpoints; Phase 3 fills
them in. Each module's prefix and tags are fixed here.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from . import __version__, audit_log, auth, ui
from .config import settings
from .metrics import auth_total, request_duration
from .modules import (
    audit as audit_module,
    backups,
    config_diff,
    containers,
    credentials,
    regression,
    registry,
    services,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("control-plane")

app = FastAPI(
    title="Operator Control Plane",
    version=__version__,
    docs_url="/docs",
    redoc_url=None,
)


@app.middleware("http")
async def instrument(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(elapsed)
    return response


# ── Liveness + metrics ────────────────────────────────────────────────
@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"status": "ok", "version": __version__}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── Auth surface ──────────────────────────────────────────────────────
class UnlockRequest(BaseModel):
    password: str


@app.post("/auth/unlock")
async def auth_unlock(payload: UnlockRequest, request: Request) -> dict[str, Any]:
    """Verify operator password against the Argon2 hash from Vault.
    On success, open the Tier 3 sliding window for this client IP.
    """
    ident = auth.require_tier1(request)  # tailnet gate
    ok = auth.verify_password_and_unlock(request, payload.password)
    outcome = "success" if ok else "fail"
    auth_total.labels(tier="3", outcome=outcome).inc()
    audit_log.emit(
        action="auth.unlock",
        tier=3,
        outcome=outcome,
        actor_ip=ident.client_ip,
        tier3_active=ok,
    )
    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid password")
    return {
        "tier3_active": True,
        "remaining_seconds": auth.tier3_remaining_seconds(request),
    }


@app.post("/auth/lock")
async def auth_lock(request: Request) -> dict[str, Any]:
    ident = auth.require_tier1(request)
    auth.lock_tier3(request)
    audit_log.emit(
        action="auth.lock",
        tier=1,
        outcome="success",
        actor_ip=ident.client_ip,
        tier3_active=False,
    )
    return {"tier3_active": False}


@app.get("/auth/status")
async def auth_status(request: Request) -> dict[str, Any]:
    ident = auth.get_identity(request)
    return {
        "client_ip": ident.client_ip,
        "is_tailnet": ident.is_tailnet,
        "tier3_active": ident.tier3_active,
        "tier3_remaining_seconds": auth.tier3_remaining_seconds(request),
    }


# ── Module routers ────────────────────────────────────────────────────
app.include_router(containers.router, prefix="/api/containers", tags=["containers"])
app.include_router(backups.router, prefix="/api/backups", tags=["backups"])
app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(audit_module.router, prefix="/api/audit", tags=["audit"])
app.include_router(config_diff.router, prefix="/api/config", tags=["config"])
app.include_router(regression.router, prefix="/api/regression", tags=["regression"])
app.include_router(registry.router, prefix="/api/registry", tags=["registry"])

# ── HTMX UI ───────────────────────────────────────────────────────────
_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.include_router(ui.router, tags=["ui"])
