"""Phase 2 entry schema validation report."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.canonical_job_schema import CanonicalJob  # noqa: E402
from framework.canonical_session_schema import CanonicalSession  # noqa: E402
from framework.phase2_session_bundle import build_phase2_session_bundle  # noqa: E402
from framework.tool_action_observation_contract import (  # noqa: E402
    ToolActionRecord,
    ToolContractName,
    ToolContractStatus,
    ToolObservationRecord,
)
from framework.tool_contract_builders import (  # noqa: E402
    build_blocked_tool_observation,
    build_tool_action,
    build_tool_observation,
)


REQUIRED_TOOLS = {
    "READ_FILE",
    "SEARCH",
    "LIST_DIR",
    "REPO_MAP",
    "APPLY_PATCH",
    "GIT_DIFF",
    "RUN_COMMAND",
    "RUN_TESTS",
    "PUBLISH_ARTIFACT",
}

REQUIRED_BUNDLE_KEYS = {
    "session",
    "jobs",
    "tool_trace",
    "permission_decisions",
    "final_outcome",
}


def generate_phase2_schema_entry_validation_report() -> dict[str, Any]:
    contracts_present = True
    try:
        session = CanonicalSession(session_id="phase2-entry-s", task_id="phase2-entry-t")
        session_dict = session.to_dict()
        serialization_session_ok = isinstance(session_dict, dict) and session_dict["session_id"] == "phase2-entry-s"
    except Exception:
        contracts_present = False
        serialization_session_ok = False

    try:
        job = CanonicalJob.from_session(session, job_id="phase2-entry-j")
        job_dict = job.to_dict()
        serialization_job_ok = (
            isinstance(job_dict, dict)
            and job_dict["job_id"] == "phase2-entry-j"
            and job_dict["session_id"] == "phase2-entry-s"
        )
    except Exception:
        contracts_present = False
        serialization_job_ok = False
        job = None  # type: ignore[assignment]

    required_tools_present = REQUIRED_TOOLS.issubset(
        {member.name for member in ToolContractName}
    )

    try:
        action = build_tool_action(
            action_id="a1",
            session_id="phase2-entry-s",
            job_id="phase2-entry-j",
            tool_name=ToolContractName.READ_FILE,
            arguments={"path": "README.md"},
        )
        allowed_obs = build_tool_observation(
            action=action,
            status=ToolContractStatus.EXECUTED,
            allowed=True,
            duration_ms=1,
            stdout="ok",
            side_effect_metadata={"path": "README.md"},
        )
        blocked_obs = build_blocked_tool_observation(action=action, reason="denied_by_test")
        serialization_tool_ok = (
            isinstance(action, ToolActionRecord)
            and isinstance(allowed_obs, ToolObservationRecord)
            and isinstance(action.to_dict(), dict)
            and isinstance(allowed_obs.to_dict(), dict)
        )
        blocked_ok = (
            blocked_obs.allowed is False
            and blocked_obs.status == ToolContractStatus.BLOCKED
        )
    except Exception:
        serialization_tool_ok = False
        blocked_ok = False
        action = None  # type: ignore[assignment]
        allowed_obs = None  # type: ignore[assignment]
        blocked_obs = None  # type: ignore[assignment]

    try:
        bundle = build_phase2_session_bundle(
            session=session,
            jobs=[job] if job is not None else [],
            tool_actions=[action] if action is not None else [],
            tool_observations=[allowed_obs, blocked_obs]
            if allowed_obs is not None and blocked_obs is not None
            else [],
            permission_decisions=[{"reason": "test"}],
            final_outcome="completed",
        )
        bundle_shape_ok = REQUIRED_BUNDLE_KEYS.issubset(set(bundle.keys()))
    except Exception:
        bundle_shape_ok = False

    serialization_ok = (
        serialization_session_ok and serialization_job_ok and serialization_tool_ok
    )

    all_checks_pass = (
        contracts_present
        and required_tools_present
        and serialization_ok
        and blocked_ok
        and bundle_shape_ok
    )

    return {
        "phase2_entry_check": "phase2_schema_entry",
        "contracts_present": contracts_present,
        "required_tools_present": required_tools_present,
        "serialization_ok": serialization_ok,
        "blocked_observation_ok": blocked_ok,
        "bundle_shape_ok": bundle_shape_ok,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase2_schema_entry_validation_report()
    print(report)
    sys.exit(0 if report.get("all_checks_pass") else 1)
