"""Inference abstraction layer for local-first worker runtime."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import urllib.error
import urllib.request
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


class OllamaInferenceAdapter:
    """Adapter that calls a local Ollama instance via /api/chat.

    Falls back to LocalHeuristicInferenceAdapter on any network or parse failure.
    Reads OLLAMA_API_BASE and OLLAMA_MODEL env vars (same pattern as bin/aider_local.sh).
    """

    def __init__(
        self,
        profile: BackendProfile,
        *,
        base_url: str = "",
        model: str = "",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.profile = profile
        self._base_url = (base_url.rstrip("/") or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")).rstrip("/")
        self._model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b")
        self._timeout = float(timeout_seconds)
        self._fallback = LocalHeuristicInferenceAdapter(profile)
        self._semaphore = threading.BoundedSemaphore(value=max(1, profile.max_inference_concurrency))

    def run(self, request: InferenceRequest) -> InferenceResponse:
        with self._semaphore:
            try:
                body = json.dumps({
                    "model": self._model,
                    "messages": [{"role": "user", "content": request.prompt}],
                    "stream": False,
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"{self._base_url}/api/chat",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    raw = resp.read()
                payload = json.loads(raw)
                output_text = str(payload.get("message", {}).get("content") or "")
                return InferenceResponse(
                    backend=f"ollama:{self._model}",
                    output_text=output_text,
                    metadata={
                        "model": self._model,
                        "base_url": self._base_url,
                        "job_id": request.job_id,
                    },
                )
            except Exception:
                return self._fallback.run(request)


class ClaudeCodeCLIInferenceAdapter:
    """Adapter that calls the local `claude` CLI in --print mode.

    Falls back to LocalHeuristicInferenceAdapter on any subprocess or parse failure.
    Uses --dangerously-skip-permissions so no interactive confirmation is needed.
    """

    def __init__(self, profile: BackendProfile, *, timeout_seconds: float = 120.0) -> None:
        self.profile = profile
        self._timeout = float(timeout_seconds)
        self._fallback = LocalHeuristicInferenceAdapter(profile)
        self._semaphore = threading.BoundedSemaphore(value=max(1, profile.max_inference_concurrency))

    def run(self, request: InferenceRequest) -> InferenceResponse:
        with self._semaphore:
            prompt = request.prompt.strip()
            if not prompt:
                return self._fallback.run(request)
            try:
                proc = subprocess.run(
                    [
                        "claude",
                        "-p", prompt,
                        "--output-format", "text",
                        "--dangerously-skip-permissions",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    encoding="utf-8",
                    errors="replace",
                )
                output_text = proc.stdout.strip()
                if proc.returncode != 0 or not output_text:
                    return self._fallback.run(request)
                return InferenceResponse(
                    backend="claude_code_cli",
                    output_text=output_text,
                    metadata={"job_id": request.job_id, "returncode": proc.returncode},
                )
            except Exception:
                return self._fallback.run(request)


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
    if mode == "ollama":
        return OllamaInferenceAdapter(profile=profile)
    if mode == "claude_code_cli":
        return ClaudeCodeCLIInferenceAdapter(profile=profile)
    if mode == "artifact_replay" and replay_path:
        return ArtifactReplayInferenceAdapter(profile=profile, replay_path=Path(replay_path).resolve())
    return LocalHeuristicInferenceAdapter(profile=profile)
