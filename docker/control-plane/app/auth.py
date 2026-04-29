"""Tailnet IP gate, Argon2 password verification, Tier 3 sliding-window session.

Trust model:
  - Caddy is the outer door. Caddy's `@tailnet remote_ip 100.64.0.0/10`
    matcher rejects off-tailnet requests with 403 before they reach
    this app. We re-check here as defense-in-depth.
  - Tailnet identity is read from X-Forwarded-For (set by Caddy from
    the real client IP). We treat any tailnet IP as a valid Tier 1+2
    identity. We do not currently look up the Headscale node — IP is
    sufficient for single-operator scale.
  - Tier 3 escalation: operator submits the password, we verify
    against the Argon2 hash, set a per-IP `tier3_unlocked_until`
    timestamp. Each Tier 3 action checks the timestamp.

Single-process / single-worker is assumed. Sessions live in memory
and are lost on restart (acceptable: operator re-auths).
"""
from __future__ import annotations

import ipaddress
import logging
import time
from dataclasses import dataclass
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import HTTPException, Request, status

from .config import settings

log = logging.getLogger(__name__)
_hasher = PasswordHasher()
_tailnet = ipaddress.ip_network(settings.tailnet_cidr)

# session_id (== client IP for now) → tier3_unlocked_until (epoch seconds)
_tier3_sessions: dict[str, float] = {}


@dataclass(frozen=True)
class Identity:
    client_ip: str
    is_tailnet: bool
    tier3_active: bool


def _client_ip(request: Request) -> str:
    """Extract the client IP. Caddy is configured with
    `header_up X-Forwarded-For {remote_host}` so the real client
    IP arrives as the X-F-F header. Fall back to the socket peer.
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        # First IP in the list is the original client
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def get_identity(request: Request) -> Identity:
    ip_str = _client_ip(request)
    is_tailnet = False
    if ip_str:
        try:
            is_tailnet = ipaddress.ip_address(ip_str) in _tailnet
        except ValueError:
            is_tailnet = False

    tier3_active = False
    until = _tier3_sessions.get(ip_str, 0)
    if until > time.time():
        tier3_active = True

    return Identity(client_ip=ip_str, is_tailnet=is_tailnet, tier3_active=tier3_active)


def require_tier1(request: Request) -> Identity:
    """T1 read-only. Tailnet identity sufficient."""
    ident = get_identity(request)
    if settings.require_tailnet and not ident.is_tailnet:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "tailnet required")
    return ident


def require_tier2(request: Request) -> Identity:
    """T2 safe actions. Same gate as T1 today."""
    return require_tier1(request)


def require_tier3(request: Request) -> Identity:
    """T3 sensitive actions. Tailnet + active operator re-auth window."""
    ident = require_tier1(request)
    if not ident.tier3_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="tier3-reauth-required",
            headers={"WWW-Authenticate": 'Tier3Reauth realm="control-plane"'},
        )
    return ident


def verify_password_and_unlock(request: Request, password: str) -> bool:
    """Verify operator password against the Vault-stored Argon2 hash.
    On success, unlock Tier 3 for this client IP for the configured
    window. Returns True on success.
    """
    if not settings.operator_argon2_hash:
        log.error("operator_argon2_hash empty — Vault Agent template did not render")
        return False

    try:
        _hasher.verify(settings.operator_argon2_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        log.exception("operator hash format invalid")
        return False

    ip = _client_ip(request)
    _tier3_sessions[ip] = time.time() + settings.tier3_window_seconds
    return True


def lock_tier3(request: Request) -> None:
    """Explicit lock — used by /auth/lock for operator-initiated
    deescalation."""
    ip = _client_ip(request)
    _tier3_sessions.pop(ip, None)


def tier3_remaining_seconds(request: Request) -> int:
    ip = _client_ip(request)
    until = _tier3_sessions.get(ip, 0)
    return max(0, int(until - time.time()))
