"""Audit + log search — Vault audit / Caddy access / control-plane actions.

All three log sources are JSON Lines. Tail-only reads (cap by line
count + max bytes) keep memory bounded. The Vault audit log file is
mounted RO from `vault_vault-logs`; Caddy access log from `caddy-logs`;
control-plane actions written by this app to `actions_log_path`.

Routes (all T1):
  GET /api/audit/vault?tail=N&q=...
  GET /api/audit/caddy?tail=N&q=...
  GET /api/audit/actions?tail=N&q=...
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from .. import audit_log
from ..auth import Identity, require_tier1
from ..config import settings
from ..metrics import actions_total

log = logging.getLogger(__name__)
router = APIRouter()

# Cap each tail read at this many bytes to bound memory usage.
_MAX_BYTES = 4 * 1024 * 1024  # 4 MiB


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


def _tail_lines(path: Path, max_lines: int) -> list[str]:
    """Return the last `max_lines` lines of `path`, capped at _MAX_BYTES."""
    if not path.exists():
        return []
    size = path.stat().st_size
    read = min(size, _MAX_BYTES)
    with path.open("rb") as fh:
        if size > read:
            fh.seek(size - read)
        buf = fh.read(read)
    text = buf.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if size > read:
        # First line may be partial; drop it.
        lines = lines[1:]
    return lines[-max_lines:]


def _filter(lines: Iterable[str], q: str | None) -> Iterable[str]:
    if not q:
        return lines
    qlow = q.lower()
    return (ln for ln in lines if qlow in ln.lower())


def _parse_jsonl(lines: Iterable[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            out.append({"_raw": ln})
    return out


@router.get("/vault")
async def vault_audit(
    request: Request,
    tail: int = Query(default=200, ge=1, le=2000),
    q: str | None = Query(default=None),
    ident: Identity = Depends(require_tier1),
) -> dict[str, Any]:
    p = Path(settings.audit_log_path)
    try:
        lines = _tail_lines(p, tail * 4 if q else tail)
    except OSError as e:
        _record("audit.vault", ident, "fail", error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "vault audit unreadable")
    matched = list(_filter(lines, q))[-tail:]
    parsed = _parse_jsonl(matched)
    # Project to a digestible shape: time, type, request.path, request.operation
    proj = []
    for e in parsed:
        if "_raw" in e:
            proj.append(e)
            continue
        req = e.get("request", {}) or {}
        auth = e.get("auth", {}) or {}
        proj.append(
            {
                "time": e.get("time"),
                "type": e.get("type"),
                "operation": req.get("operation"),
                "path": req.get("path"),
                "remote_ip": req.get("remote_address"),
                "role_name": (auth.get("metadata") or {}).get("role_name"),
                "policies": auth.get("token_policies"),
            }
        )
    _record("audit.vault", ident, "success", returned=len(proj))
    return {"source": "vault", "events": proj, "returned": len(proj)}


@router.get("/caddy")
async def caddy_access(
    request: Request,
    tail: int = Query(default=200, ge=1, le=2000),
    q: str | None = Query(default=None),
    ident: Identity = Depends(require_tier1),
) -> dict[str, Any]:
    p = Path(settings.caddy_access_log_path)
    try:
        lines = _tail_lines(p, tail * 4 if q else tail)
    except OSError as e:
        _record("audit.caddy", ident, "fail", error=str(e))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "caddy access unreadable")
    matched = list(_filter(lines, q))[-tail:]
    parsed = _parse_jsonl(matched)
    proj = []
    for e in parsed:
        if "_raw" in e:
            proj.append(e)
            continue
        req = e.get("request", {}) or {}
        proj.append(
            {
                "ts": e.get("ts"),
                "host": req.get("host"),
                "method": req.get("method"),
                "uri": req.get("uri"),
                "remote_ip": req.get("remote_ip"),
                "status": e.get("status"),
                "size": e.get("size"),
                "duration": e.get("duration"),
                "user_agent": (req.get("headers") or {}).get("User-Agent", [""])[0],
            }
        )
    _record("audit.caddy", ident, "success", returned=len(proj))
    return {"source": "caddy", "events": proj, "returned": len(proj)}


@router.get("/actions")
async def actions(
    request: Request,
    tail: int = Query(default=200, ge=1, le=2000),
    q: str | None = Query(default=None),
    ident: Identity = Depends(require_tier1),
) -> dict[str, Any]:
    p = Path(settings.actions_log_path)
    try:
        lines = _tail_lines(p, tail * 4 if q else tail)
    except OSError as e:
        _record("audit.actions", ident, "fail", error=str(e))
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "action log unreadable"
        )
    matched = list(_filter(lines, q))[-tail:]
    parsed = _parse_jsonl(matched)
    _record("audit.actions", ident, "success", returned=len(parsed))
    return {"source": "actions", "events": parsed, "returned": len(parsed)}
