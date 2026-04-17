from typing import Any


def detect_completion_boundary(
    closure_result: dict[str, Any],
    telemetry_result: dict[str, Any],
    phase_result: dict[str, Any],
    audit_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(closure_result, dict)
        or not isinstance(telemetry_result, dict)
        or not isinstance(phase_result, dict)
        or not isinstance(audit_result, dict)
    ):
        return {
            "boundary_valid": False,
            "closure_complete": False,
            "telemetry_complete": False,
            "phase_complete": False,
            "audit_complete": False,
            "boundary_crossed": False,
            "open_conditions": [],
            "boundary_status": "invalid_input",
        }

    closure_complete = closure_result.get("closure_status") == "closed"
    telemetry_complete = telemetry_result.get("gap_status") == "complete"
    phase_complete = phase_result.get("phase_completion_pct", 0) == 100
    audit_complete = audit_result.get("audit_status") == "passed"

    conditions = []
    if not closure_complete:
        conditions.append("closure_complete")
    if not telemetry_complete:
        conditions.append("telemetry_complete")
    if not phase_complete:
        conditions.append("phase_complete")
    if not audit_complete:
        conditions.append("audit_complete")

    boundary_crossed = len(conditions) == 0

    if boundary_crossed:
        status = "clean"
    elif len(conditions) <= 2:
        status = "partial"
    else:
        status = "open"

    return {
        "boundary_valid": True,
        "closure_complete": closure_complete,
        "telemetry_complete": telemetry_complete,
        "phase_complete": phase_complete,
        "audit_complete": audit_complete,
        "boundary_crossed": boundary_crossed,
        "open_conditions": conditions,
        "boundary_status": status,
    }


def summarize_completion_boundary(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("boundary_valid") is not True:
        return {
            "summary_valid": False,
            "boundary_status": "invalid_input",
            "boundary_crossed": False,
            "open_condition_count": 0,
        }

    return {
        "summary_valid": True,
        "boundary_status": result.get("boundary_status", "invalid_input"),
        "boundary_crossed": bool(result.get("boundary_crossed", False)),
        "open_condition_count": (
            len(result.get("open_conditions", []))
            if isinstance(result.get("open_conditions", []), list)
            else 0
        ),
    }
