from typing import Any


def finalize_coordination(
    governance_cp: dict[str, Any],
    resilience_cp: dict[str, Any],
    recovery_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(governance_cp, dict)
        or not isinstance(resilience_cp, dict)
        or not isinstance(recovery_cp, dict)
    ):
        return {
            "finalization_status": "invalid_input",
            "finalized_phase": None,
            "operational_count": 0,
        }

    gov_op = governance_cp.get("governance_cp_status") == "operational"
    res_op = resilience_cp.get("resilience_cp_status") == "operational"
    rec_op = recovery_cp.get("recovery_cp_status") == "operational"

    all_operational = gov_op and res_op and rec_op
    any_operational = gov_op or res_op or rec_op
    op_count = sum([gov_op, res_op, rec_op])

    if all_operational:
        return {
            "finalization_status": "finalized",
            "finalized_phase": governance_cp.get("governance_phase"),
            "operational_count": op_count,
        }

    if any_operational and not all_operational:
        return {
            "finalization_status": "pending",
            "finalized_phase": None,
            "operational_count": op_count,
        }

    return {
        "finalization_status": "blocked",
        "finalized_phase": None,
        "operational_count": op_count,
    }
