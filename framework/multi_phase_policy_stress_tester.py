from typing import Any


def stress_test_policy(
    adversarial_results: dict[str, Any],
    refinement: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(adversarial_results, dict)
        or not isinstance(refinement, dict)
        or not isinstance(config, dict)
    ):
        return {
            "stress_status": "invalid_input",
            "stress_level": None,
            "stress_result": None,
        }

    ar_ok = adversarial_results.get("adversarial_status") == "tested"
    r_ok = refinement.get("refinement_status") == "refined"
    all_ok = ar_ok and r_ok

    if all_ok:
        return {
            "stress_status": "stressed",
            "stress_level": config.get("level", "high"),
            "stress_result": "stressed_complete",
        }

    return {
        "stress_status": "failed",
        "stress_level": None,
        "stress_result": None,
    }
