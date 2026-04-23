"""Inference abstraction layer for local-first worker runtime."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from .backend_profiles import BackendProfile, get_backend_profile
from .compat import UTC


@dataclass(frozen=True)
class InferenceRequest:
    job_id: str
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InferenceResponse:
    backend: str
    output_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class InferenceAdapter(Protocol):
    """Stable interface consumed by worker runtime."""

    profile: BackendProfile

    def run(self, request: InferenceRequest) -> InferenceResponse:
        raise NotImplementedError


class LocalHeuristicInferenceAdapter:
    """Baseline adapter for local deterministic scaffolding.

    This is intentionally lightweight so worker logic never couples to a specific
    model runner. Swapping to ollama/vllm/remote gRPC should only require a new
    adapter implementing the same interface.
    """

    def __init__(self, profile: BackendProfile) -> None:
        self.profile = profile
        self._semaphore = threading.BoundedSemaphore(value=max(1, profile.max_inference_concurrency))

    def run(self, request: InferenceRequest) -> InferenceResponse:
        with self._semaphore:
            prompt = request.prompt.strip()
            guidance = {
                "job_id": request.job_id,
                "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "context_keys": sorted(request.context.keys()),
            }
            if not prompt:
                text = "No inference prompt provided. Proceed with local action execution only."
            elif len(prompt) > 500:
                text = "Prompt is long; execute bounded plan and emit artifacts for follow-up refinement."
            else:
                text = f"Bounded execution guidance: {prompt[:220]}"
            return InferenceResponse(backend=self.profile.name, output_text=text, metadata=guidance)


class ArtifactReplayInferenceAdapter:
    """Adapter that replays a previously captured response artifact when present."""

    def __init__(self, profile: BackendProfile, replay_path: Path) -> None:
        self.profile = profile
        self._delegate = LocalHeuristicInferenceAdapter(profile)
        self._replay_path = replay_path

    def run(self, request: InferenceRequest) -> InferenceResponse:
        if self._replay_path.exists():
            try:
                payload = json.loads(self._replay_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict) and str(payload.get("output_text") or ""):
                return InferenceResponse(
                    backend=f"{self.profile.name}:artifact_replay",
                    output_text=str(payload.get("output_text")),
                    metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
                )
        return self._delegate.run(request)


def build_inference_adapter(
    *,
    backend_profile: str,
    mode: str = "heuristic",
    replay_path: str = "",
) -> InferenceAdapter:
    profile = get_backend_profile(backend_profile)
    if mode == "artifact_replay" and replay_path:
        return ArtifactReplayInferenceAdapter(profile=profile, replay_path=Path(replay_path).resolve())
    return LocalHeuristicInferenceAdapter(profile=profile)
