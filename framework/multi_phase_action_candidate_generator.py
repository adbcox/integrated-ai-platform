from typing import Any


def generate_action_candidates(
    intent: dict[str, Any],
    optimization_cp: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(intent, dict)
        or not isinstance(optimization_cp, dict)
        or not isinstance(forecast, dict)
    ):
        return {
            "candidate_status": "invalid_input",
            "candidate_count": 0,
            "candidate_phase": None,
        }

    intent_ok = intent.get("intent_status") == "extracted"
    opt_op = optimization_cp.get("optimization_cp_status") == "operational"
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if intent_ok and opt_op and forecast_ok:
        return {
            "candidate_status": "generated",
            "candidate_count": 3,
            "candidate_phase": intent.get("extracted_phase"),
        }

    if not intent_ok:
        return {
            "candidate_status": "no_intent",
            "candidate_count": 0,
            "candidate_phase": None,
        }

    return {
        "candidate_status": "invalid_input",
        "candidate_count": 0,
        "candidate_phase": None,
    }
