from typing import Any


def report_adaptation(
    validation: dict[str, Any],
    closed_loop: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(closed_loop, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "adaptation_report_status": "invalid_input",
            "report_phase": None,
            "loop_status": None,
            "adaptation_complete": False,
        }

    if validation.get("adaptation_validation_status") != "valid":
        return {
            "adaptation_report_status": "incomplete",
            "report_phase": None,
            "loop_status": None,
            "adaptation_complete": False,
        }

    return {
        "adaptation_report_status": "complete",
        "report_phase": phase_id,
        "loop_status": closed_loop.get("loop_status"),
        "adaptation_complete": validation.get("adaptation_complete", False),
    }
