"""GatewayInferenceAdapter — InferenceAdapter-compatible wrapper for InferenceGateway.

Satisfies the InferenceAdapter protocol by duck typing so WorkerRuntime /
Scheduler can use the Phase 1 gateway without modification.
"""

from __future__ import annotations

from typing import Any

from .backend_profiles import BackendProfile
from .gateway_executors import build_gateway_for_env
from .inference_adapter import InferenceRequest, InferenceResponse
from .inference_gateway import GatewayRequest, InferenceGateway

BACKEND_TO_GATEWAY_PROFILE: dict[str, str] = {
    "mac_local": "fast",
    "threadripper_local": "balanced",
    "multi_host_future": "hard",
}

_FALLBACK_PROFILE = "balanced"


class GatewayInferenceAdapter:
    """InferenceAdapter duck-type wrapper around InferenceGateway."""

    def __init__(self, profile: BackendProfile, gateway: InferenceGateway) -> None:
        self.profile = profile
        self._gateway = gateway
        self._gateway_profile_name = BACKEND_TO_GATEWAY_PROFILE.get(
            profile.name, _FALLBACK_PROFILE
        )

    def run(self, request: InferenceRequest) -> InferenceResponse:
        gateway_request = GatewayRequest(
            profile_name=self._gateway_profile_name,
            prompt=request.prompt,
            context=dict(request.context),
            requested_by=request.job_id,
        )
        resp = self._gateway.invoke(gateway_request)
        telemetry_dict: dict[str, Any] = {}
        if resp.telemetry is not None:
            try:
                telemetry_dict = resp.telemetry.to_dict()
            except Exception:  # noqa: BLE001
                telemetry_dict = {}
        metadata: dict[str, Any] = {
            "success": resp.success,
            "telemetry": telemetry_dict,
        }
        if not resp.success and resp.error:
            metadata["error"] = resp.error
        return InferenceResponse(
            backend=self.profile.name,
            output_text=resp.output_text if resp.success else "",
            metadata=metadata,
        )


def build_gateway_adapter(
    profile: BackendProfile,
    *,
    force_heuristic: bool = False,
    base_url: str = "",
) -> GatewayInferenceAdapter:
    gateway = build_gateway_for_env(
        force_heuristic=force_heuristic,
        base_url=base_url,
    )
    return GatewayInferenceAdapter(profile=profile, gateway=gateway)


__all__ = ["GatewayInferenceAdapter", "build_gateway_adapter", "BACKEND_TO_GATEWAY_PROFILE"]
