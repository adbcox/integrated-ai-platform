from typing import Any


def schedule_difficulty(
    progression: dict[str, Any],
    curriculum: dict[str, Any],
    scheduling_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(progression, dict)
        or not isinstance(curriculum, dict)
        or not isinstance(scheduling_config, dict)
    ):
        return {
            "difficulty_status": "invalid_input",
            "difficulty_phase": None,
            "difficulty_level": None,
        }

    progression_ok = progression.get("progression_status") == "tracked"
    curriculum_ok = curriculum.get("curriculum_status") == "shaped"

    if progression_ok and curriculum_ok:
        return {
            "difficulty_status": "scheduled",
            "difficulty_phase": progression.get("progression_phase"),
            "difficulty_level": scheduling_config.get("level", "medium"),
        }

    if not progression_ok:
        return {
            "difficulty_status": "no_progression",
            "difficulty_phase": None,
            "difficulty_level": None,
        }

    return {
        "difficulty_status": "invalid_input",
        "difficulty_phase": None,
        "difficulty_level": None,
    }
