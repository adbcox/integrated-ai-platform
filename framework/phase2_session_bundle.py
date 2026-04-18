"""Phase 2 entry: deterministic session bundler."""

from __future__ import annotations

from typing import Any, Iterable

from framework.canonical_job_schema import CanonicalJob
from framework.canonical_session_schema import CanonicalSession
from framework.tool_action_observation_contract import (
    ToolActionRecord,
    ToolObservationRecord,
)


def build_phase2_session_bundle(
    *,
    session: CanonicalSession,
    jobs: Iterable[CanonicalJob] = (),
    tool_actions: Iterable[ToolActionRecord] = (),
    tool_observations: Iterable[ToolObservationRecord] = (),
    permission_decisions: Iterable[dict[str, Any]] = (),
    final_outcome: str = "",
) -> dict[str, Any]:
    action_entries = [a.to_dict() for a in tool_actions]
    observation_entries = [o.to_dict() for o in tool_observations]
    tool_trace: list[dict[str, Any]] = []
    for entry in action_entries:
        tool_trace.append({"kind": "tool_action", **entry})
    for entry in observation_entries:
        tool_trace.append({"kind": "tool_observation", **entry})
    return {
        "session": session.to_dict(),
        "jobs": [job.to_dict() for job in jobs],
        "tool_trace": tool_trace,
        "permission_decisions": [dict(d) for d in permission_decisions],
        "final_outcome": final_outcome or session.final_outcome,
    }


__all__ = ["build_phase2_session_bundle"]
