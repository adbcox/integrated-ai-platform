from typing import Any


def shape_resources(
    predictive_balance: dict[str, Any],
    resource_tracker: dict[str, Any],
    shaping_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(predictive_balance, dict)
        or not isinstance(resource_tracker, dict)
        or not isinstance(shaping_config, dict)
    ):
        return {
            "shaping_status": "invalid_input",
            "shaped_phase": None,
            "resource_count": 0,
        }

    balance_ok = predictive_balance.get("balancing_status") in (
        "rebalanced",
        "holding",
    )
    res_ok = int(resource_tracker.get("phase_count", 0)) > 0

    if not balance_ok:
        return {
            "shaping_status": "no_rebalance",
            "shaped_phase": None,
            "resource_count": 0,
        }

    if balance_ok and res_ok:
        return {
            "shaping_status": "shaped",
            "shaped_phase": resource_tracker.get("tracked_phase"),
            "resource_count": int(resource_tracker.get("phase_count", 0)),
        }

    return {
        "shaping_status": "invalid_input",
        "shaped_phase": None,
        "resource_count": 0,
    }
