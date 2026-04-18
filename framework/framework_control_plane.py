"""Manager / control-plane helpers for consuming Phase 2 runtime payload.

All helpers are additive. No legacy keys are removed or renamed.
"""

from __future__ import annotations

from typing import Any

# ------------------------------------------------------------------ #
# Phase 2 payload detection and extraction helpers                     #
# ------------------------------------------------------------------ #

_PHASE2_REQUIRED_KEYS = frozenset(
    {
        "canonical_session",
        "canonical_jobs",
        "typed_tool_trace",
        "permission_decisions",
        "session_bundle",
        "final_outcome",
    }
)


def _phase2_manager_present(payload: dict[str, Any]) -> bool:
    """Return True iff *payload* contains all Phase 2 runtime keys."""
    return all(k in payload for k in _PHASE2_REQUIRED_KEYS)


def _phase2_manager_tool_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic summary of the typed tool trace in *payload*."""
    trace = payload.get("typed_tool_trace") or []
    tool_names: set[str] = set()
    blocked = 0
    executed = 0
    failed = 0
    for entry in trace:
        try:
            name = str(entry.get("tool_name") or entry.get("contract_name") or "").strip()
            status = str(entry.get("status") or "").strip()
        except Exception:
            continue
        if name:
            tool_names.add(name)
        if status == "blocked":
            blocked += 1
        elif status == "executed":
            executed += 1
        elif status == "failed":
            failed += 1
    return {
        "tool_count": len(tool_names),
        "tool_names_sorted": sorted(tool_names),
        "blocked_count": blocked,
        "executed_count": executed,
        "failed_count": failed,
    }


def _phase2_manager_extract(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a normalized Phase 2 manager view from a runtime result payload.

    Always returns a complete dict. If the Phase 2 surface is absent the
    ``phase2_payload_present`` flag is ``False`` and summaries are empty.
    """
    _empty_tool_summary: dict[str, Any] = {
        "tool_count": 0,
        "tool_names_sorted": [],
        "blocked_count": 0,
        "executed_count": 0,
        "failed_count": 0,
    }

    if not _phase2_manager_present(payload):
        return {
            "phase2_payload_present": False,
            "canonical_session_summary": {},
            "canonical_job_summaries": [],
            "typed_tool_summary": _empty_tool_summary,
            "permission_decision_count": 0,
            "final_outcome": str(
                payload.get("final_outcome") or payload.get("status") or ""
            ),
        }

    canonical_session: dict[str, Any] = payload.get("canonical_session") or {}
    canonical_jobs: list[Any] = payload.get("canonical_jobs") or []
    permission_decisions: list[Any] = payload.get("permission_decisions") or []

    canonical_session_summary: dict[str, Any] = {
        "session_id": str(canonical_session.get("session_id") or ""),
        "task_id": str(canonical_session.get("task_id") or ""),
        "selected_runtime": str(canonical_session.get("selected_runtime") or ""),
        "selected_model_profile": str(
            canonical_session.get("selected_model_profile") or ""
        ),
        "final_outcome": str(canonical_session.get("final_outcome") or ""),
    }

    canonical_job_summaries: list[dict[str, Any]] = []
    for job_dict in canonical_jobs:
        if not isinstance(job_dict, dict):
            continue
        canonical_job_summaries.append(
            {
                "job_id": str(job_dict.get("job_id") or ""),
                "session_id": str(job_dict.get("session_id") or ""),
                "status": str(job_dict.get("status") or ""),
                "final_outcome": str(job_dict.get("final_outcome") or ""),
            }
        )

    return {
        "phase2_payload_present": True,
        "canonical_session_summary": canonical_session_summary,
        "canonical_job_summaries": canonical_job_summaries,
        "typed_tool_summary": _phase2_manager_tool_summary(payload),
        "permission_decision_count": len(permission_decisions),
        "final_outcome": str(payload.get("final_outcome") or ""),
    }


# ------------------------------------------------------------------ #
# Bounded control-plane integration point                              #
# ------------------------------------------------------------------ #

def run_managed_job(job: Any, *, runtime: Any) -> dict[str, Any]:
    """Execute *job* on *runtime* and append ``phase2_manager_view``.

    This is the narrowest integration point that emits the runtime result
    payload. ``phase2_manager_view`` is appended additively; no legacy keys
    are removed or renamed.
    """
    payload: dict[str, Any] = runtime._execute_job(job)
    payload["phase2_manager_view"] = _phase2_manager_extract(payload)
    return payload


def _phase2_manager_decision(manager_view: dict[str, Any]) -> dict[str, Any]:
    """Derive a deterministic operational signal from a phase2_manager_view dict.

    Returns a dict with keys: signal, reason, blocked_count,
    executed_count, tool_count, final_outcome.
    signal is one of: ok | all_tools_blocked | no_tools_ran |
    partial_block | phase2_absent.
    """
    if not manager_view.get("phase2_payload_present"):
        return {
            "signal": "phase2_absent",
            "reason": "phase2 payload not present in result",
            "blocked_count": 0,
            "executed_count": 0,
            "tool_count": 0,
            "final_outcome": str(manager_view.get("final_outcome") or ""),
        }
    tool_summary = manager_view.get("typed_tool_summary") or {}
    tool_count = int(tool_summary.get("tool_count") or 0)
    blocked_count = int(tool_summary.get("blocked_count") or 0)
    executed_count = int(tool_summary.get("executed_count") or 0)
    final_outcome = str(manager_view.get("final_outcome") or "")
    if tool_count == 0:
        signal, reason = "no_tools_ran", "no typed tool observations recorded"
    elif blocked_count > 0 and executed_count == 0:
        signal, reason = "all_tools_blocked", "all tool attempts were blocked by permission engine"
    elif blocked_count > 0 and executed_count > 0:
        signal, reason = "partial_block", "some tool attempts were blocked; some executed"
    else:
        signal, reason = "ok", "all observed tools executed without block"
    return {
        "signal": signal,
        "reason": reason,
        "blocked_count": blocked_count,
        "executed_count": executed_count,
        "tool_count": tool_count,
        "final_outcome": final_outcome,
    }


__all__ = [
    "_phase2_manager_present",
    "_phase2_manager_tool_summary",
    "_phase2_manager_extract",
    "_phase2_manager_decision",
    "run_managed_job",
]
