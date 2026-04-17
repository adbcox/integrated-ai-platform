from typing import Any


def gate_cross_planes(
    autonomy_cp: dict[str, Any],
    optimization_cp: dict[str, Any],
    observability_cp: dict[str, Any],
    governance_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(autonomy_cp, dict)
        or not isinstance(optimization_cp, dict)
        or not isinstance(observability_cp, dict)
        or not isinstance(governance_cp, dict)
    ):
        return {
            "cross_plane_status": "invalid_input",
            "aligned_phase": None,
            "active_planes": 0,
        }

    aut_op = autonomy_cp.get("autonomy_cp_status") == "operational"
    opt_op = optimization_cp.get("optimization_cp_status") == "operational"
    obs_op = observability_cp.get("observability_cp_status") == "operational"
    gov_op = governance_cp.get("governance_cp_status") == "operational"

    all_ok = aut_op and opt_op and obs_op and gov_op
    any_ok = aut_op or opt_op or obs_op or gov_op
    active_planes = sum([aut_op, opt_op, obs_op, gov_op])

    if all_ok:
        return {
            "cross_plane_status": "aligned",
            "aligned_phase": autonomy_cp.get("autonomy_phase"),
            "active_planes": active_planes,
        }

    if any_ok:
        return {
            "cross_plane_status": "partial",
            "aligned_phase": None,
            "active_planes": active_planes,
        }

    return {
        "cross_plane_status": "misaligned",
        "aligned_phase": None,
        "active_planes": active_planes,
    }
