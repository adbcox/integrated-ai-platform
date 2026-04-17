from typing import Any


def execute_reconciliation(
    plan: dict[str, Any],
    control_plane: dict[str, Any],
    resource_tracker: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(plan, dict)
        or not isinstance(control_plane, dict)
        or not isinstance(resource_tracker, dict)
    ):
        return {
            "execution_status": "invalid_input",
            "executed_phase": None,
            "resource_count": 0,
        }

    if plan.get("reconciliation_status") != "planned":
        return {
            "execution_status": "no_plan",
            "executed_phase": None,
            "resource_count": 0,
        }

    if control_plane.get("control_plane_status") != "operational":
        return {
            "execution_status": "control_plane_not_operational",
            "executed_phase": None,
            "resource_count": int(resource_tracker.get("phase_count", 0)),
        }

    if int(resource_tracker.get("phase_count", 0)) <= 0:
        return {
            "execution_status": "no_resources",
            "executed_phase": None,
            "resource_count": 0,
        }

    return {
        "execution_status": "executed",
        "executed_phase": plan.get("reconciliation_phase"),
        "resource_count": int(resource_tracker.get("phase_count", 0)),
    }
