from typing import Any


def report_governance(
    validation: dict[str, Any],
    watchdog: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(watchdog, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "governance_report_status": "invalid_input",
            "report_phase": None,
            "watchdog_status": None,
            "governance_complete": False,
        }

    if validation.get("governance_validation_status") != "valid":
        return {
            "governance_report_status": "incomplete",
            "report_phase": None,
            "watchdog_status": None,
            "governance_complete": False,
        }

    return {
        "governance_report_status": "complete",
        "report_phase": phase_id,
        "watchdog_status": watchdog.get("watchdog_status"),
        "governance_complete": validation.get("governance_complete", False),
    }
