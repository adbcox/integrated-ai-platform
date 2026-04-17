from typing import Any


def generate_recommendations(
    synthesis: dict[str, Any],
    forecast: dict[str, Any],
    recommendation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(synthesis, dict)
        or not isinstance(forecast, dict)
        or not isinstance(recommendation_config, dict)
    ):
        return {
            "recommendation_status": "invalid_input",
            "recommendation_phase": None,
            "recommendation_count": 0,
        }

    synth_ok = synthesis.get("synthesis_status") == "synthesized"
    forecast_ok = forecast.get("forecast_status") == "forecasted"

    if synth_ok and forecast_ok:
        return {
            "recommendation_status": "generated",
            "recommendation_phase": synthesis.get("synthesis_phase"),
            "recommendation_count": synthesis.get("knowledge_count", 0),
        }

    if not synth_ok:
        return {
            "recommendation_status": "no_synthesis",
            "recommendation_phase": None,
            "recommendation_count": 0,
        }

    return {
        "recommendation_status": "invalid_input",
        "recommendation_phase": None,
        "recommendation_count": 0,
    }
