from typing import Any


def gate_cross_layer_learning(
    learning_cp: dict[str, Any],
    autonomy_cp: dict[str, Any],
    optimization_cp: dict[str, Any],
    observability_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(learning_cp, dict)
        or not isinstance(autonomy_cp, dict)
        or not isinstance(optimization_cp, dict)
        or not isinstance(observability_cp, dict)
    ):
        return {
            "cross_layer_status": "invalid_input",
            "aligned_phase": None,
            "active_planes": 0,
        }

    learn_op = learning_cp.get("learning_cp_status") == "operational"
    aut_op = autonomy_cp.get("autonomy_cp_status") == "operational"
    opt_op = optimization_cp.get("optimization_cp_status") == "operational"
    obs_op = observability_cp.get("observability_cp_status") == "operational"
    all_ok = learn_op and aut_op and opt_op and obs_op
    any_ok = learn_op or aut_op or opt_op or obs_op
    active_planes = sum([learn_op, aut_op, opt_op, obs_op])

    if all_ok:
        return {
            "cross_layer_status": "aligned",
            "aligned_phase": learning_cp.get("learning_phase"),
            "active_planes": active_planes,
        }

    if any_ok:
        return {
            "cross_layer_status": "partial",
            "aligned_phase": None,
            "active_planes": active_planes,
        }

    return {
        "cross_layer_status": "misaligned",
        "aligned_phase": None,
        "active_planes": active_planes,
    }
