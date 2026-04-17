from typing import Any


def plan_horizon(
    generalization: dict[str, Any],
    forecast: dict[str, Any],
    horizon_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization, dict)
        or not isinstance(forecast, dict)
        or not isinstance(horizon_config, dict)
    ):
        return {
            "horizon_plan_status": "invalid_input",
            "horizon_phase": None,
            "horizon_depth": 0,
        }

    generalization_ok = generalization.get("generalization_status") == "generalized"
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if generalization_ok and forecast_ok:
        return {
            "horizon_plan_status": "planned",
            "horizon_phase": generalization.get("generalization_phase"),
            "horizon_depth": horizon_config.get("depth", 10),
        }

    if not generalization_ok:
        return {
            "horizon_plan_status": "no_generalization",
            "horizon_phase": None,
            "horizon_depth": 0,
        }

    return {
        "horizon_plan_status": "invalid_input",
        "horizon_phase": None,
        "horizon_depth": 0,
    }
