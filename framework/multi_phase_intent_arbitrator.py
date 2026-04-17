from typing import Any


def arbitrate_intents(
    negotiation: dict[str, Any],
    governance_cp: dict[str, Any],
    arbitration_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(negotiation, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(arbitration_policy, dict)
    ):
        return {
            "arbitration_status": "invalid_input",
            "arbitrated_phase": None,
            "arbitrated_action": None,
        }

    neg_ok = negotiation.get("negotiation_status") == "negotiated"
    gov_op = governance_cp.get("governance_cp_status") == "operational"

    if neg_ok and gov_op:
        return {
            "arbitration_status": "arbitrated",
            "arbitrated_phase": governance_cp.get("governance_phase"),
            "arbitrated_action": negotiation.get("negotiated_action"),
        }

    if neg_ok and not gov_op:
        return {
            "arbitration_status": "governance_blocked",
            "arbitrated_phase": None,
            "arbitrated_action": None,
        }

    return {
        "arbitration_status": "no_negotiation",
        "arbitrated_phase": None,
        "arbitrated_action": None,
    }
