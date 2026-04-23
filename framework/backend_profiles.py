"""Backend profile definitions for bounded-concurrency inference backends."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .compat import StrEnum


class BackendProfileName(StrEnum):
    MAC_LOCAL = "mac_local"
    THREADRIPPER_LOCAL = "threadripper_local"
    MULTI_HOST_FUTURE = "multi_host_future"


@dataclass(frozen=True)
class BackendProfile:
    name: str
    max_inference_concurrency: int
    max_worker_concurrency: int
    notes: str
    max_active_jobs_by_task_class: dict[str, int] = field(default_factory=dict)


BACKEND_PROFILES: dict[str, BackendProfile] = {
    BackendProfileName.MAC_LOCAL.value: BackendProfile(
        name=BackendProfileName.MAC_LOCAL.value,
        max_inference_concurrency=2,
        max_worker_concurrency=3,
        notes="Unified-memory local profile tuned for bounded thermal/concurrency behavior.",
        max_active_jobs_by_task_class={
            "validation_check_execution": 1,
            "benchmark_analysis": 1,
        },
    ),
    BackendProfileName.THREADRIPPER_LOCAL.value: BackendProfile(
        name=BackendProfileName.THREADRIPPER_LOCAL.value,
        max_inference_concurrency=4,
        max_worker_concurrency=8,
        notes="Higher CPU/RAM local profile for heavier parallel execution.",
        max_active_jobs_by_task_class={
            "validation_check_execution": 2,
            "benchmark_analysis": 2,
        },
    ),
    BackendProfileName.MULTI_HOST_FUTURE.value: BackendProfile(
        name=BackendProfileName.MULTI_HOST_FUTURE.value,
        max_inference_concurrency=8,
        max_worker_concurrency=16,
        notes="Forward-compatible placeholder profile for distributed worker hosts.",
        max_active_jobs_by_task_class={
            "validation_check_execution": 4,
            "benchmark_analysis": 4,
        },
    ),
}


def get_backend_profile(name: str) -> BackendProfile:
    return BACKEND_PROFILES.get(name) or BACKEND_PROFILES[BackendProfileName.MAC_LOCAL.value]


def select_backend_profile_auto() -> BackendProfile:
    """Choose a backend profile from local host capacity when caller asks for auto mode."""
    cpu_count = max(1, int(os.cpu_count() or 1))
    if cpu_count >= 24:
        return BACKEND_PROFILES[BackendProfileName.THREADRIPPER_LOCAL.value]
    return BACKEND_PROFILES[BackendProfileName.MAC_LOCAL.value]
