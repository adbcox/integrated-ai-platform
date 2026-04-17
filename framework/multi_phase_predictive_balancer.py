from typing import Any


def balance_predictively(
    forecast: dict[str, Any],
    load_balance: dict[str, Any],
    predictive_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(forecast, dict)
        or not isinstance(load_balance, dict)
        or not isinstance(predictive_policy, dict)
    ):
        return {
            "balancing_status": "invalid_input",
            "balanced_phase": None,
            "projected_load": 0,
        }

    forecast_ok = forecast.get("forecast_status") == "forecasted"
    lb_ok = load_balance.get("balance_status") in ("balanced", "overloaded")

    if not forecast_ok:
        return {
            "balancing_status": "no_forecast",
            "balanced_phase": None,
            "projected_load": 0,
        }

    if (
        forecast_ok
        and lb_ok
        and load_balance.get("balance_status") == "overloaded"
    ):
        return {
            "balancing_status": "rebalanced",
            "balanced_phase": load_balance.get("active_phase"),
            "projected_load": int(forecast.get("projected_load", 0)),
        }

    if (
        forecast_ok
        and lb_ok
        and load_balance.get("balance_status") == "balanced"
    ):
        return {
            "balancing_status": "holding",
            "balanced_phase": None,
            "projected_load": int(forecast.get("projected_load", 0)),
        }

    return {
        "balancing_status": "invalid_input",
        "balanced_phase": None,
        "projected_load": 0,
    }
