from typing import Any


def learn_strategy(
    knowledge: dict[str, Any],
    decision_rollup: dict[str, Any],
    strategy_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(knowledge, dict)
        or not isinstance(decision_rollup, dict)
        or not isinstance(strategy_config, dict)
    ):
        return {
            "strategy_status": "invalid_input",
            "strategy_phase": None,
            "strategy_type": None,
        }

    knowledge_ok = knowledge.get("synthesis_status") == "synthesized"
    rollup_ok = decision_rollup.get("decision_rollup_status") == "rolled_up"

    if knowledge_ok and rollup_ok:
        return {
            "strategy_status": "learned",
            "strategy_phase": knowledge.get("synthesis_phase"),
            "strategy_type": strategy_config.get("type", "reinforcement"),
        }

    if not knowledge_ok:
        return {
            "strategy_status": "no_knowledge",
            "strategy_phase": None,
            "strategy_type": None,
        }

    return {
        "strategy_status": "invalid_input",
        "strategy_phase": None,
        "strategy_type": None,
    }
