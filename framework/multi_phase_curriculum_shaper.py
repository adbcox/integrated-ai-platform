from typing import Any


def shape_curriculum(
    propagation: dict[str, Any],
    forecast: dict[str, Any],
    curriculum_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(propagation, dict)
        or not isinstance(forecast, dict)
        or not isinstance(curriculum_config, dict)
    ):
        return {
            "curriculum_status": "invalid_input",
            "curriculum_phase": None,
            "module_count": 0,
        }

    propagation_ok = propagation.get("propagation_status") == "propagated"
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if propagation_ok and forecast_ok:
        return {
            "curriculum_status": "shaped",
            "curriculum_phase": propagation.get("propagated_phase"),
            "module_count": curriculum_config.get("modules", 3),
        }

    if not propagation_ok:
        return {
            "curriculum_status": "no_propagation",
            "curriculum_phase": None,
            "module_count": 0,
        }

    return {
        "curriculum_status": "invalid_input",
        "curriculum_phase": None,
        "module_count": 0,
    }
