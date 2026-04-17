from typing import Any


def summarize_optimization(
    optimization_cp: dict[str, Any],
    forecast: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(optimization_cp, dict)
        or not isinstance(forecast, dict)
        or not isinstance(profile, dict)
    ):
        return {
            "optimization_summary_status": "invalid_input",
            "summary_phase": None,
            "optimization_health": "degraded",
        }

    cp_op = optimization_cp.get("optimization_cp_status") == "operational"
    forecast_ok = forecast.get("forecast_status") == "forecasted"
    profile_ok = profile.get("profile_status") == "profiled"

    if cp_op and forecast_ok and profile_ok:
        return {
            "optimization_summary_status": "complete",
            "summary_phase": optimization_cp.get("optimization_phase"),
            "optimization_health": "healthy",
        }

    if cp_op and (not forecast_ok or not profile_ok):
        return {
            "optimization_summary_status": "partial",
            "summary_phase": None,
            "optimization_health": "degraded",
        }

    return {
        "optimization_summary_status": "failed",
        "summary_phase": None,
        "optimization_health": "degraded",
    }
