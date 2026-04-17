from typing import Any


def extract_pattern(
    knowledge: dict[str, Any], lesson: dict[str, Any], pattern_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(knowledge, dict)
        or not isinstance(lesson, dict)
        or not isinstance(pattern_config, dict)
    ):
        return {
            "pattern_status": "invalid_input",
            "pattern_phase": None,
            "pattern_count": 0,
        }

    knowledge_ok = knowledge.get("synthesis_status") == "synthesized"
    lesson_ok = lesson.get("lesson_status") == "extracted"

    if knowledge_ok and lesson_ok:
        return {
            "pattern_status": "extracted",
            "pattern_phase": knowledge.get("synthesis_phase"),
            "pattern_count": knowledge.get("knowledge_count", 0),
        }

    if not knowledge_ok:
        return {
            "pattern_status": "no_knowledge",
            "pattern_phase": None,
            "pattern_count": 0,
        }

    return {
        "pattern_status": "invalid_input",
        "pattern_phase": None,
        "pattern_count": 0,
    }
