from typing import Any


def report_learning(
    validation: dict[str, Any], recommendation: dict[str, Any], phase_id: str
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(recommendation, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "learning_report_status": "invalid_input",
            "report_phase": None,
            "recommendation_count": 0,
            "learning_complete": False,
        }

    if validation.get("learning_validation_status") == "valid":
        return {
            "learning_report_status": "complete",
            "report_phase": phase_id,
            "recommendation_count": recommendation.get("recommendation_count", 0),
            "learning_complete": validation.get("learning_complete", False),
        }

    return {
        "learning_report_status": "incomplete",
        "report_phase": None,
        "recommendation_count": 0,
        "learning_complete": False,
    }
