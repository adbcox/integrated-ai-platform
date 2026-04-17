from typing import Any


def generate_scenarios(
    generalization_engine: dict[str, Any],
    forecast_model: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization_engine, dict)
        or not isinstance(forecast_model, dict)
        or not isinstance(config, dict)
    ):
        return {
            "scenario_status": "invalid_input",
            "scenario_count": 0,
            "scenario_phase": None,
        }

    ge_ok = generalization_engine.get("generalization_status") == "generalized"
    fm_ok = forecast_model.get("forecast_status") == "forecasted"
    all_ok = ge_ok and fm_ok

    if all_ok:
        return {
            "scenario_status": "generated",
            "scenario_count": config.get("count", 5),
            "scenario_phase": generalization_engine.get("generalization_phase"),
        }

    return {
        "scenario_status": "failed",
        "scenario_count": 0,
        "scenario_phase": None,
    }
