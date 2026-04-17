from typing import Any


def refine_policy(
    strategy: dict[str, Any],
    policy_selection: dict[str, Any],
    refinement_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(strategy, dict)
        or not isinstance(policy_selection, dict)
        or not isinstance(refinement_config, dict)
    ):
        return {
            "refinement_status": "invalid_input",
            "refined_phase": None,
            "original_policy": None,
        }

    strategy_ok = strategy.get("strategy_status") == "learned"
    policy_ok = policy_selection.get("policy_selection_status") == "selected"

    if strategy_ok and policy_ok:
        return {
            "refinement_status": "refined",
            "refined_phase": strategy.get("strategy_phase"),
            "original_policy": policy_selection.get("selected_policy"),
        }

    if not strategy_ok:
        return {
            "refinement_status": "no_strategy",
            "refined_phase": None,
            "original_policy": None,
        }

    return {
        "refinement_status": "invalid_input",
        "refined_phase": None,
        "original_policy": None,
    }
