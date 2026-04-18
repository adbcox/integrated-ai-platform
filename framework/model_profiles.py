"""Phase 1 typed local model profiles.

Deterministic registry of local coding profiles consumed by the internal
inference gateway (``framework.inference_gateway``). Profiles are the
only way Phase 1 local routes describe "which backend / model / budget"
to use for a given task class. No Ollama-specific shell details leak
to callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


DEFAULT_BACKEND = "ollama"


@dataclass(frozen=True)
class ModelProfile:
    profile_name: str
    backend: str
    model: str
    context_window: int
    timeout_seconds: int
    retry_budget: int
    temperature: float
    intended_task_classes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_name": self.profile_name,
            "backend": self.backend,
            "model": self.model,
            "context_window": self.context_window,
            "timeout_seconds": self.timeout_seconds,
            "retry_budget": self.retry_budget,
            "temperature": self.temperature,
            "intended_task_classes": list(self.intended_task_classes),
        }


_PROFILES: dict[str, ModelProfile] = {
    "fast": ModelProfile(
        profile_name="fast",
        backend=DEFAULT_BACKEND,
        model="qwen2.5-coder:14b",
        context_window=8192,
        timeout_seconds=90,
        retry_budget=1,
        temperature=0.2,
        intended_task_classes=(
            "quick_fix",
            "single_file_edit",
            "bounded_refactor",
        ),
    ),
    "balanced": ModelProfile(
        profile_name="balanced",
        backend=DEFAULT_BACKEND,
        model="deepseek-coder-v2",
        context_window=16384,
        timeout_seconds=180,
        retry_budget=2,
        temperature=0.2,
        intended_task_classes=(
            "multi_file_edit",
            "planning",
            "explain_code",
        ),
    ),
    "hard": ModelProfile(
        profile_name="hard",
        backend=DEFAULT_BACKEND,
        model="qwen2.5-coder:32b",
        context_window=32768,
        timeout_seconds=360,
        retry_budget=2,
        temperature=0.15,
        intended_task_classes=(
            "cross_module_refactor",
            "architecture_reasoning",
            "hard_debug",
        ),
    ),
    # Dormant placeholder for future vLLM profile. Phase 1 keeps Ollama
    # as the only active backend; no heavy integration work is attempted
    # in this packet.
    "vllm_dormant": ModelProfile(
        profile_name="vllm_dormant",
        backend="vllm",
        model="placeholder",
        context_window=0,
        timeout_seconds=0,
        retry_budget=0,
        temperature=0.0,
        intended_task_classes=(),
    ),
}


def list_active_profiles() -> list[ModelProfile]:
    """Return all non-dormant profiles in deterministic order."""
    return [p for p in _PROFILES.values() if not p.profile_name.endswith("_dormant")]


def list_profile_names() -> list[str]:
    return sorted(_PROFILES.keys())


def get_profile(name: str) -> ModelProfile:
    if name not in _PROFILES:
        raise KeyError(f"unknown profile: {name!r}")
    return _PROFILES[name]


def resolve_profile_for_task_class(task_class: str) -> ModelProfile:
    """Deterministically map a task class to a profile.

    Falls back to ``balanced`` when no profile declares the class.
    """
    for profile in list_active_profiles():
        if task_class in profile.intended_task_classes:
            return profile
    return _PROFILES["balanced"]


def iter_profiles() -> Iterable[ModelProfile]:
    return iter(_PROFILES.values())


__all__ = [
    "DEFAULT_BACKEND",
    "ModelProfile",
    "get_profile",
    "iter_profiles",
    "list_active_profiles",
    "list_profile_names",
    "resolve_profile_for_task_class",
]
