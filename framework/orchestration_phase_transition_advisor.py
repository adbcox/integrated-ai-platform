from typing import Any


def advise_phase_transition(
    phase_report: dict[str, Any],
    dashboard_result: dict[str, Any],
    health_result: dict[str, Any],
    closure_result: dict[str, Any],
    integrity_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase_report, dict)
        or not isinstance(dashboard_result, dict)
        or not isinstance(health_result, dict)
        or not isinstance(closure_result, dict)
        or not isinstance(integrity_result, dict)
    ):
        return {
            "advisor_valid": False,
            "phase_complete": False,
            "operationally_healthy": False,
            "health_ok": False,
            "lifecycle_closed": False,
            "archive_intact": False,
            "transition_ready": False,
            "blocking_conditions": [],
            "transition_recommendation": "invalid_input",
        }

    phase_complete = phase_report.get("phase_report_status") == "complete"
    operationally_healthy = (
        dashboard_result.get("overall_operational_status") == "operational"
    )
    health_ok = health_result.get("health_status") == "healthy"
    lifecycle_closed = closure_result.get("closure_status") == "closed"
    archive_intact = integrity_result.get("integrity_status") == "intact"

    blocking_conditions = []
    if not phase_complete:
        blocking_conditions.append("phase_complete")
    if not operationally_healthy:
        blocking_conditions.append("operationally_healthy")
    if not health_ok:
        blocking_conditions.append("health_ok")
    if not lifecycle_closed:
        blocking_conditions.append("lifecycle_closed")
    if not archive_intact:
        blocking_conditions.append("archive_intact")

    transition_ready = len(blocking_conditions) == 0

    if transition_ready:
        recommendation = "proceed"
    elif len(blocking_conditions) <= 2:
        recommendation = "hold"
    else:
        recommendation = "investigate"

    return {
        "advisor_valid": True,
        "phase_complete": phase_complete,
        "operationally_healthy": operationally_healthy,
        "health_ok": health_ok,
        "lifecycle_closed": lifecycle_closed,
        "archive_intact": archive_intact,
        "transition_ready": transition_ready,
        "blocking_conditions": blocking_conditions,
        "transition_recommendation": recommendation,
    }


def summarize_phase_transition(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("advisor_valid") is not True:
        return {
            "summary_valid": False,
            "transition_recommendation": "invalid_input",
            "transition_ready": False,
            "blocking_condition_count": 0,
        }

    return {
        "summary_valid": True,
        "transition_recommendation": result.get(
            "transition_recommendation", "invalid_input"
        ),
        "transition_ready": bool(result.get("transition_ready", False)),
        "blocking_condition_count": (
            len(result.get("blocking_conditions", []))
            if isinstance(result.get("blocking_conditions", []), list)
            else 0
        ),
    }
