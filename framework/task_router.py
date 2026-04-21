"""Task-class and outcome-based model/profile router.

Routes a coding task to the optimal local Ollama profile based on:
  1. Task class → base profile mapping (from ModelProfile.intended_task_classes)
  2. Historical failure rate per (task_class, profile_name) pair from LocalMemoryStore
  3. Difficulty escalation: if the base profile has a high failure rate,
     try a heavier profile before giving up locally

Ollama-first is mandatory. External models are exception-only and must be
declared with backend != "ollama" — the router will only recommend them when
all local profiles are exhausted and the task is marked allow_external=True.

Import-time assertions guard all consumed surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from framework.local_memory_store import LocalMemoryStore
from framework.model_profiles import ModelProfile, list_active_profiles, resolve_profile_for_task_class

# -- import-time interface assertions --
assert "profile_name" in ModelProfile.__dataclass_fields__, \
    "INTERFACE MISMATCH: ModelProfile.profile_name"
assert "backend" in ModelProfile.__dataclass_fields__, \
    "INTERFACE MISMATCH: ModelProfile.backend"
assert "intended_task_classes" in ModelProfile.__dataclass_fields__, \
    "INTERFACE MISMATCH: ModelProfile.intended_task_classes"
assert callable(resolve_profile_for_task_class), \
    "INTERFACE MISMATCH: resolve_profile_for_task_class not callable"
assert callable(list_active_profiles), \
    "INTERFACE MISMATCH: list_active_profiles not callable"

# Ordered escalation ladder for local profiles (fast → balanced → hard)
_ESCALATION_ORDER: list[str] = ["fast", "balanced", "hard"]

# Threshold above which a profile is considered "degraded" for this task class
_DEGRADED_FAILURE_RATE: float = 0.6


@dataclass(frozen=True)
class RoutingDecision:
    profile_name: str
    backend: str
    model: str
    task_class: str
    reason: str
    escalated: bool = False
    external: bool = False

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "backend": self.backend,
            "model": self.model,
            "task_class": self.task_class,
            "reason": self.reason,
            "escalated": self.escalated,
            "external": self.external,
        }


def _ollama_profiles_by_name() -> dict[str, ModelProfile]:
    return {
        p.profile_name: p
        for p in list_active_profiles()
        if p.backend == "ollama"
    }


def _memory_key(task_class: str, profile_name: str) -> str:
    return f"{task_class}::{profile_name}"


def route_task(
    task_class: str,
    *,
    memory_store: Optional[LocalMemoryStore] = None,
    allow_external: bool = False,
    force_profile: Optional[str] = None,
) -> RoutingDecision:
    """Select the best local profile for a task class, escalating if degraded.

    Args:
        task_class: The coding task class (e.g. "text_replacement").
        memory_store: LocalMemoryStore for historical failure rates.
            If None, a default-path store is used (read-only).
        allow_external: If True and all local profiles are degraded,
            returns an external profile as last resort. Default False.
        force_profile: If set, skip routing logic and return this profile
            (still validates it exists).

    Returns:
        RoutingDecision with the chosen profile and the reason.
    """
    store = memory_store or LocalMemoryStore()
    local_profiles = _ollama_profiles_by_name()

    # forced override
    if force_profile:
        profile = local_profiles.get(force_profile)
        if profile is None:
            # fall through to normal routing if forced profile not found locally
            pass
        else:
            return RoutingDecision(
                profile_name=profile.profile_name,
                backend=profile.backend,
                model=profile.model,
                task_class=task_class,
                reason=f"forced_profile={force_profile}",
            )

    # base profile from task class
    try:
        base_profile = resolve_profile_for_task_class(task_class)
    except Exception:
        base_profile = local_profiles.get("fast") or next(iter(local_profiles.values()))

    # check failure rate for base profile
    base_rate = _profile_failure_rate(store, task_class, base_profile.profile_name)

    if base_rate < _DEGRADED_FAILURE_RATE:
        return RoutingDecision(
            profile_name=base_profile.profile_name,
            backend=base_profile.backend,
            model=base_profile.model,
            task_class=task_class,
            reason=f"base_profile failure_rate={base_rate:.2f} < threshold",
        )

    # base profile is degraded — try escalation
    for candidate_name in _ESCALATION_ORDER:
        if candidate_name == base_profile.profile_name:
            continue
        candidate = local_profiles.get(candidate_name)
        if candidate is None:
            continue
        candidate_rate = _profile_failure_rate(store, task_class, candidate_name)
        if candidate_rate < _DEGRADED_FAILURE_RATE:
            return RoutingDecision(
                profile_name=candidate.profile_name,
                backend=candidate.backend,
                model=candidate.model,
                task_class=task_class,
                reason=(
                    f"escalated from {base_profile.profile_name} "
                    f"(failure_rate={base_rate:.2f}) to {candidate_name} "
                    f"(failure_rate={candidate_rate:.2f})"
                ),
                escalated=True,
            )

    # all local profiles degraded — external fallback if allowed
    if allow_external:
        all_profiles = {p.profile_name: p for p in list_active_profiles()}
        external = [p for p in all_profiles.values() if p.backend != "ollama"]
        if external:
            chosen = external[0]
            return RoutingDecision(
                profile_name=chosen.profile_name,
                backend=chosen.backend,
                model=chosen.model,
                task_class=task_class,
                reason="all local profiles degraded; external fallback authorized",
                escalated=True,
                external=True,
            )

    # all local profiles degraded and no external — return heaviest local as last resort
    hard = local_profiles.get("hard") or base_profile
    return RoutingDecision(
        profile_name=hard.profile_name,
        backend=hard.backend,
        model=hard.model,
        task_class=task_class,
        reason=(
            f"all local profiles degraded (base_rate={base_rate:.2f}); "
            "returning heaviest local as last resort"
        ),
        escalated=True,
    )


def _profile_failure_rate(
    store: LocalMemoryStore,
    task_class: str,
    profile_name: str,
) -> float:
    """Return failure rate for a (task_class, profile_name) pair.

    The memory store does not yet record profile_name alongside outcomes,
    so this returns the task-class-wide rate as a conservative proxy.
    Once profile tracking is added to record_mvp_loop_outcome, this function
    can be narrowed to the specific profile.
    """
    return store.failure_rate(task_kind=task_class)


def route_with_memory_update(
    task_class: str,
    *,
    memory_store: Optional[LocalMemoryStore] = None,
    allow_external: bool = False,
) -> RoutingDecision:
    """Route task and return decision. Does not mutate memory — read-only."""
    return route_task(
        task_class,
        memory_store=memory_store,
        allow_external=allow_external,
    )


__all__ = [
    "RoutingDecision",
    "route_task",
    "route_with_memory_update",
]
