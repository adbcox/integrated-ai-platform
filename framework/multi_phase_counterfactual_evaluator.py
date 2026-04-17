from typing import Any


def evaluate_counterfactual(
    policy_selection: dict[str, Any],
    forecast: dict[str, Any],
    counterfactual_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(policy_selection, dict)
        or not isinstance(forecast, dict)
        or not isinstance(counterfactual_config, dict)
    ):
        return {
            "counterfactual_status": "invalid_input",
            "counterfactual_phase": None,
            "projected_outcome": 0,
            "alternative_count": 0,
        }

    policy_ok = policy_selection.get("policy_selection_status") == "selected"
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if policy_ok and forecast_ok:
        return {
            "counterfactual_status": "evaluated",
            "counterfactual_phase": policy_selection.get("policy_phase"),
            "projected_outcome": int(forecast.get("projected_load", 0)),
            "alternative_count": int(counterfactual_config.get("alternatives", 2)),
        }

    if not policy_ok:
        return {
            "counterfactual_status": "no_policy",
            "counterfactual_phase": None,
            "projected_outcome": 0,
            "alternative_count": 0,
        }

    return {
        "counterfactual_status": "invalid_input",
        "counterfactual_phase": None,
        "projected_outcome": 0,
        "alternative_count": 0,
    }
