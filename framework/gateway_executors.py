"""Executor implementations for the Phase 1 InferenceGateway.

Provides three executor flavours:
- ``heuristic_executor``: deterministic offline placeholder; no external deps.
- ``make_ollama_executor``: real HTTP call to a local Ollama daemon.
- ``make_env_auto_executor``: probes Ollama reachability, routes accordingly.

The public factory ``build_gateway_for_env`` produces a wired
``InferenceGateway`` suitable for production or forced-offline use.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

from .inference_gateway import ExecutorFn, GatewayRequest, InferenceGateway
from .model_profiles import ModelProfile

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_PROBE_TIMEOUT = 2.0


# ---------------------------------------------------------------------------
# Heuristic executor (offline, deterministic)
# ---------------------------------------------------------------------------

def heuristic_executor(request: GatewayRequest, profile: ModelProfile) -> str:
    """Deterministic offline placeholder — never requires external services."""
    lines = request.prompt.strip().splitlines()
    head = lines[0] if lines else ""
    return (
        f"[heuristic] profile={profile.profile_name} "
        f"model={profile.model} head={head[:80]!r}"
    )


# ---------------------------------------------------------------------------
# Ollama probe
# ---------------------------------------------------------------------------

def _probe_ollama(base_url: str, timeout: float = _PROBE_TIMEOUT) -> bool:
    """Return True if Ollama API is reachable at *base_url*."""
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Ollama HTTP executor
# ---------------------------------------------------------------------------

def make_ollama_executor(
    base_url: str = "",
    *,
    model_override: str = "",
) -> ExecutorFn:
    """Return an executor that calls Ollama ``/api/chat``.

    The model is taken from the ``ModelProfile`` unless *model_override* is
    given. Raises ``RuntimeError`` on HTTP or parse errors so the gateway
    can record them in telemetry without crashing.
    """
    resolved_base = (base_url or DEFAULT_OLLAMA_BASE_URL).rstrip("/")

    def _executor(request: GatewayRequest, profile: ModelProfile) -> str:
        model = model_override or profile.model
        url = resolved_base + "/api/chat"
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
            "options": {"temperature": profile.temperature},
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=profile.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Ollama HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama unreachable: {exc.reason}") from exc
        try:
            data = json.loads(body)
            return data["message"]["content"]
        except (KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama response parse error: {exc}") from exc

    return _executor


# ---------------------------------------------------------------------------
# env-auto executor (probe → Ollama or heuristic)
# ---------------------------------------------------------------------------

def make_env_auto_executor(base_url: str = "") -> ExecutorFn:
    """Probe Ollama; route to it if reachable, fall back to heuristic if not.

    The probe runs once at call time (executor construction), not per request,
    so the routing decision is stable for the lifetime of the executor.
    """
    resolved_base = base_url or DEFAULT_OLLAMA_BASE_URL
    if _probe_ollama(resolved_base):
        return make_ollama_executor(resolved_base)
    return heuristic_executor


# ---------------------------------------------------------------------------
# Production factory
# ---------------------------------------------------------------------------

def build_gateway_for_env(
    *,
    base_url: str = "",
    force_heuristic: bool = False,
) -> InferenceGateway:
    """Return a wired ``InferenceGateway`` for the current environment.

    *force_heuristic=True* bypasses Ollama probing — useful for CI and
    offline test runs that must not wait for a network timeout.
    """
    if force_heuristic:
        executor: ExecutorFn = heuristic_executor
    else:
        executor = make_env_auto_executor(base_url)
    return InferenceGateway(executor=executor)


__all__ = [
    "DEFAULT_OLLAMA_BASE_URL",
    "build_gateway_for_env",
    "heuristic_executor",
    "make_env_auto_executor",
    "make_ollama_executor",
]
