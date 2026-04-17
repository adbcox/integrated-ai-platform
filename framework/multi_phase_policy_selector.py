from typing import Any


def select_adaptive_policy(
    arbitration: dict[str, Any],
    observability_cp: dict[str, Any],
    policy_catalog: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(arbitration, dict)
        or not isinstance(observability_cp, dict)
        or not isinstance(policy_catalog, dict)
    ):
        return {
            "policy_selection_status": "invalid_input",
            "selected_policy": None,
            "policy_phase": None,
        }

    arb_ok = arbitration.get("arbitration_status") == "arbitrated"
    obs_op = observability_cp.get("observability_cp_status") == "operational"
    catalog_ok = len(policy_catalog) > 0

    if arb_ok and obs_op and catalog_ok:
        return {
            "policy_selection_status": "selected",
            "selected_policy": list(policy_catalog.keys())[0],
            "policy_phase": observability_cp.get("observability_phase"),
        }

    if arb_ok and not obs_op:
        return {
            "policy_selection_status": "observability_offline",
            "selected_policy": None,
            "policy_phase": None,
        }

    if not arb_ok:
        return {
            "policy_selection_status": "no_arbitration",
            "selected_policy": None,
            "policy_phase": None,
        }

    return {
        "policy_selection_status": "invalid_input",
        "selected_policy": None,
        "policy_phase": None,
    }
