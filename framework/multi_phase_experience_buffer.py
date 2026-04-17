from typing import Any


def buffer_experience(
    lesson: dict[str, Any], outcome: dict[str, Any], buffer_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(lesson, dict)
        or not isinstance(outcome, dict)
        or not isinstance(buffer_config, dict)
    ):
        return {
            "buffer_status": "invalid_input",
            "buffer_size": 0,
            "buffer_phase": None,
            "capacity": 0,
        }

    lesson_ok = lesson.get("lesson_status") == "extracted"
    outcome_ok = outcome.get("outcome_status") == "collected"
    max_size = buffer_config.get("max_size", 100)

    if lesson_ok and outcome_ok and max_size > 0:
        return {
            "buffer_status": "buffered",
            "buffer_size": 1,
            "buffer_phase": lesson.get("lesson_phase"),
            "capacity": max_size,
        }

    if not lesson_ok:
        return {
            "buffer_status": "no_lesson",
            "buffer_size": 0,
            "buffer_phase": None,
            "capacity": 0,
        }

    return {
        "buffer_status": "invalid_input",
        "buffer_size": 0,
        "buffer_phase": None,
        "capacity": 0,
    }
