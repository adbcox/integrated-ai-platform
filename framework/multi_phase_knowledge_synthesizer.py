from typing import Any


def synthesize_knowledge(
    retrieval: dict[str, Any],
    lessons: dict[str, Any],
    synthesis_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(retrieval, dict)
        or not isinstance(lessons, dict)
        or not isinstance(synthesis_config, dict)
    ):
        return {
            "synthesis_status": "invalid_input",
            "synthesis_phase": None,
            "knowledge_count": 0,
        }

    retrieval_ok = retrieval.get("retrieval_status") == "retrieved"
    lesson_ok = lessons.get("lesson_status") == "extracted"

    if retrieval_ok and lesson_ok:
        return {
            "synthesis_status": "synthesized",
            "synthesis_phase": retrieval.get("retrieved_phase"),
            "knowledge_count": retrieval.get("retrieved_count", 0)
            + lessons.get("lesson_count", 0),
        }

    if not retrieval_ok:
        return {
            "synthesis_status": "no_retrieval",
            "synthesis_phase": None,
            "knowledge_count": 0,
        }

    return {
        "synthesis_status": "invalid_input",
        "synthesis_phase": None,
        "knowledge_count": 0,
    }
