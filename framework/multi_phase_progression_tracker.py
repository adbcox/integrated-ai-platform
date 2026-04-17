from typing import Any


def track_progression(
    curriculum: dict[str, Any],
    decision_rollup: dict[str, Any],
    tracking_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(curriculum, dict)
        or not isinstance(decision_rollup, dict)
        or not isinstance(tracking_config, dict)
    ):
        return {
            "progression_status": "invalid_input",
            "progression_phase": None,
            "progress_level": None,
        }

    curriculum_ok = curriculum.get("curriculum_status") == "shaped"
    rollup_ok = decision_rollup.get("decision_rollup_status") == "rolled_up"

    if curriculum_ok and rollup_ok:
        return {
            "progression_status": "tracked",
            "progression_phase": curriculum.get("curriculum_phase"),
            "progress_level": tracking_config.get("level", "initial"),
        }

    if not curriculum_ok:
        return {
            "progression_status": "no_curriculum",
            "progression_phase": None,
            "progress_level": None,
        }

    return {
        "progression_status": "invalid_input",
        "progression_phase": None,
        "progress_level": None,
    }
