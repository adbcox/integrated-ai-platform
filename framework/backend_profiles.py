"""Backend profile definitions for bounded-concurrency inference backends."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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


BACKEND_PROFILES: dict[str, BackendProfile] = {
    BackendProfileName.MAC_LOCAL.value: BackendProfile(
        name=BackendProfileName.MAC_LOCAL.value,
        max_inference_concurrency=2,
        max_worker_concurrency=3,
        notes="Unified-memory local profile tuned for bounded thermal/concurrency behavior.",
    ),
    BackendProfileName.THREADRIPPER_LOCAL.value: BackendProfile(
        name=BackendProfileName.THREADRIPPER_LOCAL.value,
        max_inference_concurrency=4,
        max_worker_concurrency=8,
        notes="Higher CPU/RAM local profile for heavier parallel execution.",
    ),
    BackendProfileName.MULTI_HOST_FUTURE.value: BackendProfile(
        name=BackendProfileName.MULTI_HOST_FUTURE.value,
        max_inference_concurrency=8,
        max_worker_concurrency=16,
        notes="Forward-compatible placeholder profile for distributed worker hosts.",
    ),
}


def get_backend_profile(name: str) -> BackendProfile:
    return BACKEND_PROFILES.get(name) or BACKEND_PROFILES[BackendProfileName.MAC_LOCAL.value]
