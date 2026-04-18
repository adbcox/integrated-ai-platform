"""Phase 1 internal inference gateway.

Single internal API for local model invocation. Business logic does
not need to know Ollama-specific shell details; it configures a
``GatewayRequest`` by profile name and receives a ``GatewayResponse``
plus normalized ``InferenceTelemetry``.

Phase 1 scope only:
- Ollama is the default active backend.
- A dormant vLLM profile is allowed but not wired to any runtime here.
- No typed tool contract. Tool integration belongs to Phase 2.

The gateway supports an injectable ``executor`` callable so tests and
the baseline validation pack can exercise request/telemetry shaping
deterministically without requiring an actual local Ollama daemon.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from .model_profiles import ModelProfile, get_profile
from .runtime_telemetry_schema import InferenceTelemetry


@dataclass(frozen=True)
class GatewayRequest:
    profile_name: str
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    requested_by: str = "internal"


@dataclass(frozen=True)
class GatewayResponse:
    profile_name: str
    backend: str
    model: str
    output_text: str
    success: bool
    error: str
    telemetry: InferenceTelemetry

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "backend": self.backend,
            "model": self.model,
            "output_text": self.output_text,
            "success": self.success,
            "error": self.error,
            "telemetry": self.telemetry.to_dict(),
        }


ExecutorFn = Callable[[GatewayRequest, ModelProfile], str]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def _default_executor(request: GatewayRequest, profile: ModelProfile) -> str:
    """Stub executor used when no backend adapter is provided.

    Phase 1 intentionally keeps this a local-only placeholder. Callers
    wanting a real Ollama invocation inject an executor that shells out
    to ``ollama run <model>``; the baseline validation pack does not
    require a live daemon.
    """
    prompt_summary = request.prompt.strip().splitlines()[0:1]
    head = prompt_summary[0] if prompt_summary else ""
    return (
        f"[inference_gateway stub] profile={profile.profile_name} "
        f"backend={profile.backend} model={profile.model} head={head[:80]}"
    )


class InferenceGateway:
    """Single internal entrypoint for local model invocation."""

    def __init__(self, *, executor: ExecutorFn | None = None) -> None:
        self._executor = executor or _default_executor

    def resolve(self, profile_name: str) -> ModelProfile:
        return get_profile(profile_name)

    def invoke(self, request: GatewayRequest) -> GatewayResponse:
        profile = self.resolve(request.profile_name)
        started_at = _iso_now()
        t0 = perf_counter()
        prompt_hash = _hash_prompt(request.prompt)
        success = True
        error = ""
        output_text = ""
        try:
            output_text = self._executor(request, profile)
        except Exception as exc:  # noqa: BLE001 - gateway must report, not raise
            success = False
            error = f"{type(exc).__name__}: {exc}"
        completed_at = _iso_now()
        duration_ms = int((perf_counter() - t0) * 1000)
        telemetry = InferenceTelemetry(
            profile_name=profile.profile_name,
            backend=profile.backend,
            model=profile.model,
            timeout_seconds=profile.timeout_seconds,
            retry_budget=profile.retry_budget,
            prompt_hash=prompt_hash,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )
        return GatewayResponse(
            profile_name=profile.profile_name,
            backend=profile.backend,
            model=profile.model,
            output_text=output_text,
            success=success,
            error=error,
            telemetry=telemetry,
        )


__all__ = [
    "ExecutorFn",
    "GatewayRequest",
    "GatewayResponse",
    "InferenceGateway",
]
