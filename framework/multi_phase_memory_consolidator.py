from typing import Any


def consolidate_memory(
    memory_store: dict[str, Any],
    knowledge_synthesizer: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(memory_store, dict)
        or not isinstance(knowledge_synthesizer, dict)
        or not isinstance(config, dict)
    ):
        return {
            "consolidation_status": "invalid_input",
            "consolidated_count": 0,
            "consolidation_phase": None,
        }

    ms_ok = memory_store.get("memory_status") == "stored"
    ks_ok = knowledge_synthesizer.get("synthesis_status") == "synthesized"
    all_ok = ms_ok and ks_ok

    if all_ok:
        return {
            "consolidation_status": "consolidated",
            "consolidated_count": memory_store.get("stored_count", 0),
            "consolidation_phase": memory_store.get("memory_phase"),
        }

    return {
        "consolidation_status": "failed",
        "consolidated_count": 0,
        "consolidation_phase": None,
    }
