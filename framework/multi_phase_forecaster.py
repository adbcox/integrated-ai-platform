from typing import Any


def forecast_phase_load(
    trend: dict[str, Any],
    capacity_plan: dict[str, Any],
    horizon_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(trend, dict)
        or not isinstance(capacity_plan, dict)
        or not isinstance(horizon_config, dict)
    ):
        return {
            "forecast_status": "invalid_input",
            "forecast_phase": None,
            "horizon": 0,
            "projected_load": 0,
        }

    trend_ok = trend.get("trend_status") == "analyzed"
    capacity_ok = capacity_plan.get("capacity_status") in ("planned", "at_capacity")

    if trend_ok and capacity_ok:
        return {
            "forecast_status": "forecasted",
            "forecast_phase": trend.get("trend_phase"),
            "horizon": int(horizon_config.get("horizon", 5)),
            "projected_load": int(capacity_plan.get("demand_count", 0)),
        }

    if not trend_ok:
        return {
            "forecast_status": "no_trend",
            "forecast_phase": None,
            "horizon": 0,
            "projected_load": 0,
        }

    return {
        "forecast_status": "invalid_input",
        "forecast_phase": None,
        "horizon": 0,
        "projected_load": 0,
    }
