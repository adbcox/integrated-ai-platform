from typing import Any


def feedback_learning(
    summary: dict[str, Any], lessons: dict[str, Any], feedback_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(summary, dict)
        or not isinstance(lessons, dict)
        or not isinstance(feedback_config, dict)
    ):
        return {
            "learning_feedback_status": "invalid_input",
            "feedback_phase": None,
            "lessons_fed": 0,
        }

    summary_ok = summary.get("intelligence_summary_status") in ("complete", "partial")
    lesson_ok = lessons.get("lesson_status") == "extracted"

    if summary_ok and lesson_ok:
        return {
            "learning_feedback_status": "fed_back",
            "feedback_phase": summary.get("summary_phase"),
            "lessons_fed": lessons.get("lesson_count", 0),
        }

    if not summary_ok:
        return {
            "learning_feedback_status": "no_summary",
            "feedback_phase": None,
            "lessons_fed": 0,
        }

    return {
        "learning_feedback_status": "invalid_input",
        "feedback_phase": None,
        "lessons_fed": 0,
    }
