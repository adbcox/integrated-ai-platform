from typing import Any


def report_recovery(
    validation: dict[str, Any],
    recovery_plan: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(recovery_plan, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "report_status": "invalid_input",
            "report_phase": None,
            "strategy_used": None,
            "recovery_complete": False,
        }

    if validation.get("validation_status") != "valid":
        return {
            "report_status": "incomplete",
            "report_phase": None,
            "strategy_used": None,
            "recovery_complete": False,
        }

    return {
        "report_status": "complete",
        "report_phase": phase_id,
        "strategy_used": recovery_plan.get("strategy"),
        "recovery_complete": validation.get("recovery_complete", False),
    }
