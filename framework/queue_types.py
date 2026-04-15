"""Shared queue envelope types for scheduler/worker decoupling."""

from __future__ import annotations

from dataclasses import dataclass, field

from .job_schema import Job


@dataclass(frozen=True, order=True)
class QueueEnvelope:
    """Priority-ordered queue wrapper preserving deterministic FIFO ties."""

    priority_rank: int
    sequence: int
    job: Job = field(compare=False)
