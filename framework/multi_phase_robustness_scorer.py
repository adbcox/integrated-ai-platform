from typing import Any


def score_robustness(
    simulation_results: dict[str, Any],
    mastery_assessment: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(simulation_results, dict)
        or not isinstance(mastery_assessment, dict)
        or not isinstance(config, dict)
    ):
        return {
            "robustness_status": "invalid_input",
            "robustness_score": None,
            "robustness_phase": None,
        }

    sr_ok = simulation_results.get("simulation_status") == "simulated"
    ma_ok = mastery_assessment.get("mastery_status") == "assessed"
    all_ok = sr_ok and ma_ok

    if all_ok:
        return {
            "robustness_status": "scored",
            "robustness_score": mastery_assessment.get("mastery_score"),
            "robustness_phase": simulation_results.get("simulation_phase"),
        }

    return {
        "robustness_status": "failed",
        "robustness_score": None,
        "robustness_phase": None,
    }
