from typing import Any


def extract_lessons(
    quality: dict[str, Any], recording: dict[str, Any], lesson_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(quality, dict)
        or not isinstance(recording, dict)
        or not isinstance(lesson_config, dict)
    ):
        return {
            "lesson_status": "invalid_input",
            "lesson_count": 0,
            "lesson_phase": None,
            "lesson_type": None,
        }

    quality_ok = quality.get("quality_status") == "scored"
    record_ok = recording.get("recording_status") == "recorded"

    if quality_ok and record_ok:
        lesson_type = "positive" if quality.get("quality_score", 0.0) > 0 else "negative"
        return {
            "lesson_status": "extracted",
            "lesson_count": 1,
            "lesson_phase": quality.get("quality_phase"),
            "lesson_type": lesson_type,
        }

    if not quality_ok:
        return {
            "lesson_status": "no_quality",
            "lesson_count": 0,
            "lesson_phase": None,
            "lesson_type": None,
        }

    return {
        "lesson_status": "invalid_input",
        "lesson_count": 0,
        "lesson_phase": None,
        "lesson_type": None,
    }
