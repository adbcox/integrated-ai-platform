"""Inspection-gated adapters over CanonicalSession/CanonicalJob for bounded runtime use."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from framework.canonical_session_schema import CanonicalSession
from framework.canonical_job_schema import CanonicalJob

# Inspection gate: verify required fields are present at import time
assert hasattr(CanonicalSession, "__dataclass_fields__")
assert "session_id" in CanonicalSession.__dataclass_fields__
assert hasattr(CanonicalJob, "from_session")


def make_session_adapter(
    session_id: str,
    task_id: str,
    *,
    task_class: str = "bounded_coding",
    objective: str = "",
    repo_id: str = "",
    branch: str = "",
) -> CanonicalSession:
    return CanonicalSession(
        session_id=session_id,
        task_id=task_id,
        task_class=task_class,
        objective=objective,
        repo_id=repo_id,
        branch=branch,
    )


def make_job_adapter(
    session_like: Any,
    *,
    job_id: str = "",
) -> CanonicalJob:
    if not job_id:
        job_id = f"job-{uuid4().hex[:12]}"

    if isinstance(session_like, CanonicalSession):
        return CanonicalJob.from_session(session_like, job_id)

    sid = _extract_sid(session_like)
    task_class = getattr(session_like, "task_class", "") or (
        session_like.get("task_class", "") if isinstance(session_like, dict) else ""
    )
    return CanonicalJob(
        job_id=job_id,
        session_id=sid,
        task_class=task_class,
    )


def session_to_context_dict(session_like: Any) -> dict:
    sid = _extract_sid(session_like)
    result = {"session_id": sid}
    for attr in ("task_id", "task_class", "objective", "repo_id", "branch"):
        val = _get_attr(session_like, attr)
        if val is not None:
            result[attr] = val
    return result


def _extract_sid(session_like: Any) -> str:
    if isinstance(session_like, dict):
        if "session_id" not in session_like:
            raise ValueError("session_like mapping missing 'session_id'")
        return str(session_like["session_id"])
    if hasattr(session_like, "session_id"):
        return str(session_like.session_id)
    raise ValueError(f"Cannot extract session_id from {type(session_like)!r}")


def _get_attr(obj: Any, attr: str):
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)


__all__ = ["make_session_adapter", "make_job_adapter", "session_to_context_dict"]
