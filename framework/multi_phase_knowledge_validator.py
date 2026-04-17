from typing import Any


def validate_knowledge(
    synthesis: dict[str, Any],
    strategy: dict[str, Any],
    validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(synthesis, dict)
        or not isinstance(strategy, dict)
        or not isinstance(validation_config, dict)
    ):
        return {
            "knowledge_validation_status": "invalid_input",
            "validated_phase": None,
            "knowledge_complete": False,
        }

    synth_ok = synthesis.get("synthesis_status") == "synthesized"
    strat_ok = strategy.get("strategy_status") == "learned"
    all_ok = synth_ok and strat_ok
    any_ok = synth_ok or strat_ok

    if all_ok:
        return {
            "knowledge_validation_status": "valid",
            "validated_phase": synthesis.get("synthesis_phase"),
            "knowledge_complete": True,
        }

    if any_ok:
        return {
            "knowledge_validation_status": "partial",
            "validated_phase": None,
            "knowledge_complete": False,
        }

    return {
        "knowledge_validation_status": "failed",
        "validated_phase": None,
        "knowledge_complete": False,
    }
