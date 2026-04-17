from typing import Any


def rebalance_phase_distribution(
    load_balancer: dict[str, Any],
    phase_allocation: dict[str, Any],
    rebalance_allowed: bool,
) -> dict[str, Any]:
    if (
        not isinstance(load_balancer, dict)
        or not isinstance(phase_allocation, dict)
        or not isinstance(rebalance_allowed, bool)
    ):
        return {
            "rebalance_status": "invalid_input",
            "phases_redistributed": 0,
            "rebalance_complete": False,
        }

    if load_balancer.get("load_status") not in ("overloaded", "high_load", "balanced"):
        return {
            "rebalance_status": "invalid_load_state",
            "phases_redistributed": 0,
            "rebalance_complete": False,
        }

    if not rebalance_allowed:
        return {
            "rebalance_status": "rebalance_not_allowed",
            "phases_redistributed": 0,
            "rebalance_complete": False,
        }

    if load_balancer.get("load_status") == "balanced":
        return {
            "rebalance_status": "no_rebalance_needed",
            "phases_redistributed": 0,
            "rebalance_complete": False,
        }

    phases_count = phase_allocation.get("phase_count", 0)
    if phases_count <= 1:
        return {
            "rebalance_status": "insufficient_phases",
            "phases_redistributed": 0,
            "rebalance_complete": False,
        }

    redistributed = max(1, phases_count // 2)

    return {
        "rebalance_status": "redistributed",
        "phases_redistributed": redistributed,
        "rebalance_complete": True,
    }
