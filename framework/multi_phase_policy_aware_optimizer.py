from typing import Any


def optimize_with_policy(
    tuning: dict[str, Any],
    governance_cp: dict[str, Any],
    optimization_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(tuning, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(optimization_policy, dict)
    ):
        return {
            "optimization_status": "invalid_input",
            "optimized_phase": None,
            "policy_strategy": None,
        }

    tuning_ok = tuning.get("tuning_status") == "tuned"
    gov_op = governance_cp.get("governance_cp_status") == "operational"

    if not tuning_ok:
        return {
            "optimization_status": "no_tuning",
            "optimized_phase": None,
            "policy_strategy": None,
        }

    if tuning_ok and not gov_op:
        return {
            "optimization_status": "governance_blocked",
            "optimized_phase": None,
            "policy_strategy": None,
        }

    return {
        "optimization_status": "optimized",
        "optimized_phase": governance_cp.get("governance_phase"),
        "policy_strategy": optimization_policy.get("strategy", "cost_aware"),
    }
