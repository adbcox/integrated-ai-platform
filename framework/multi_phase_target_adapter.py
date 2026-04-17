from typing import Any


def adapt_to_target(
    analysis: dict[str, Any],
    coordinator: dict[str, Any],
    adaptation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(analysis, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(adaptation_config, dict)
    ):
        return {
            "target_adaptation_status": "invalid_input",
            "adapted_phase": None,
            "adaptation_strategy": None,
        }

    analysis_ok = analysis.get("analysis_status") == "analyzed"
    coordinator_ok = coordinator.get("coordinator_status") == "initialized"

    if analysis_ok and coordinator_ok:
        return {
            "target_adaptation_status": "adapted",
            "adapted_phase": coordinator.get("phase_id"),
            "adaptation_strategy": adaptation_config.get("strategy", "gradual"),
        }

    if analysis_ok and not coordinator_ok:
        return {
            "target_adaptation_status": "coordinator_not_ready",
            "adapted_phase": None,
            "adaptation_strategy": None,
        }

    if not analysis_ok:
        return {
            "target_adaptation_status": "no_analysis",
            "adapted_phase": None,
            "adaptation_strategy": None,
        }

    return {
        "target_adaptation_status": "invalid_input",
        "adapted_phase": None,
        "adaptation_strategy": None,
    }
