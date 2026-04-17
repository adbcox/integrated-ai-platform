from typing import Any


def execute_transfer(
    target_adaptation: dict[str, Any],
    strategy: dict[str, Any],
    transfer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(target_adaptation, dict)
        or not isinstance(strategy, dict)
        or not isinstance(transfer_config, dict)
    ):
        return {
            "transfer_execution_status": "invalid_input",
            "executed_phase": None,
            "transferred_count": 0,
        }

    adaptation_ok = target_adaptation.get("target_adaptation_status") == "adapted"
    strategy_ok = strategy.get("strategy_status") == "learned"

    if adaptation_ok and strategy_ok:
        return {
            "transfer_execution_status": "executed",
            "executed_phase": target_adaptation.get("adapted_phase"),
            "transferred_count": 1,
        }

    if not adaptation_ok:
        return {
            "transfer_execution_status": "no_adaptation",
            "executed_phase": None,
            "transferred_count": 0,
        }

    return {
        "transfer_execution_status": "invalid_input",
        "executed_phase": None,
        "transferred_count": 0,
    }
