from typing import Any


def assess_mastery(
    progression: dict[str, Any],
    quality: dict[str, Any],
    mastery_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(progression, dict)
        or not isinstance(quality, dict)
        or not isinstance(mastery_config, dict)
    ):
        return {
            "mastery_status": "invalid_input",
            "mastery_phase": None,
            "mastery_level": None,
            "mastery_score": 0.0,
        }

    progression_ok = progression.get("progression_status") == "tracked"
    quality_ok = quality.get("quality_status") == "scored"
    score = quality.get("quality_score", 0.0) if quality_ok else 0.0

    if progression_ok and quality_ok:
        if score >= 0.7:
            level = "mastered"
        elif score >= 0.3:
            level = "partial"
        else:
            level = "novice"

        return {
            "mastery_status": "assessed",
            "mastery_phase": progression.get("progression_phase"),
            "mastery_level": level,
            "mastery_score": score,
        }

    if not progression_ok:
        return {
            "mastery_status": "no_progression",
            "mastery_phase": None,
            "mastery_level": None,
            "mastery_score": 0.0,
        }

    return {
        "mastery_status": "invalid_input",
        "mastery_phase": None,
        "mastery_level": None,
        "mastery_score": 0.0,
    }
