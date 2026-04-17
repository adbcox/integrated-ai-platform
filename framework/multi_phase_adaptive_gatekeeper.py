from typing import Any


def gate_adaptation(
    optimization_cp: dict[str, Any],
    observability_cp: dict[str, Any],
    governance_cp: dict[str, Any],
    finalization: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(optimization_cp, dict)
        or not isinstance(observability_cp, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(finalization, dict)
    ):
        return {
            "gatekeeper_status": "invalid_input",
            "gated_phase": None,
            "active_planes": 0,
        }

    opt_op = optimization_cp.get("optimization_cp_status") == "operational"
    obs_op = observability_cp.get("observability_cp_status") == "operational"
    gov_op = governance_cp.get("governance_cp_status") == "operational"
    fin_ok = finalization.get("finalization_status") in ("finalized", "pending")

    all_active = opt_op and obs_op and gov_op and fin_ok
    any_active = opt_op or obs_op or gov_op or fin_ok
    active_planes = sum([opt_op, obs_op, gov_op, fin_ok])

    if all_active:
        return {
            "gatekeeper_status": "open",
            "gated_phase": optimization_cp.get("optimization_phase"),
            "active_planes": active_planes,
        }

    if any_active:
        return {
            "gatekeeper_status": "partial",
            "gated_phase": None,
            "active_planes": active_planes,
        }

    return {
        "gatekeeper_status": "closed",
        "gated_phase": None,
        "active_planes": active_planes,
    }
