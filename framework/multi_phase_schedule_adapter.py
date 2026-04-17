from typing import Any


def adapt_schedule(
    forecast: dict[str, Any],
    coordinator: dict[str, Any],
    adaptation_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(forecast, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(adaptation_policy, dict)
    ):
        return {"adaptation_status": "invalid_input", "adapted_phase": None, "strategy": None}

    forecast_ok = forecast.get("forecast_status") == "forecasted"
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if not forecast_ok:
        return {
            "adaptation_status": "no_forecast",
            "adapted_phase": None,
            "strategy": None,
        }

    if forecast_ok and not coord_ok:
        return {
            "adaptation_status": "coordinator_not_ready",
            "adapted_phase": None,
            "strategy": None,
        }

    return {
        "adaptation_status": "adapted",
        "adapted_phase": coordinator.get("phase_id"),
        "strategy": adaptation_policy.get("strategy", "reactive"),
    }
