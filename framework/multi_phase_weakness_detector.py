from typing import Any


def detect_weaknesses(
    failure_modes: dict[str, Any],
    robustness_score: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(failure_modes, dict)
        or not isinstance(robustness_score, dict)
        or not isinstance(config, dict)
    ):
        return {
            "weakness_status": "invalid_input",
            "weakness_count": 0,
            "weakness_phase": None,
        }

    fm_ok = failure_modes.get("failure_catalog_status") == "cataloged"
    rs_ok = robustness_score.get("robustness_status") == "scored"
    all_ok = fm_ok and rs_ok

    if all_ok:
        return {
            "weakness_status": "detected",
            "weakness_count": failure_modes.get("failure_count", 0),
            "weakness_phase": failure_modes.get("failure_phase"),
        }

    return {
        "weakness_status": "failed",
        "weakness_count": 0,
        "weakness_phase": None,
    }
