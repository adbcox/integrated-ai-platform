from typing import Any


def propagate_knowledge(
    application: dict[str, Any],
    synthesis: dict[str, Any],
    propagation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(application, dict)
        or not isinstance(synthesis, dict)
        or not isinstance(propagation_config, dict)
    ):
        return {
            "propagation_status": "invalid_input",
            "propagated_phase": None,
            "knowledge_count": 0,
        }

    application_ok = application.get("application_status") == "applied"
    synthesis_ok = synthesis.get("synthesis_status") == "synthesized"

    if application_ok and synthesis_ok:
        return {
            "propagation_status": "propagated",
            "propagated_phase": application.get("applied_phase"),
            "knowledge_count": synthesis.get("knowledge_count", 0),
        }

    if not application_ok:
        return {
            "propagation_status": "no_application",
            "propagated_phase": None,
            "knowledge_count": 0,
        }

    return {
        "propagation_status": "invalid_input",
        "propagated_phase": None,
        "knowledge_count": 0,
    }
