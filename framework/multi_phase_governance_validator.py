from typing import Any


def validate_governance(
    policy_audit: dict[str, Any],
    sla: dict[str, Any],
    resilience_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(policy_audit, dict)
        or not isinstance(sla, dict)
        or not isinstance(resilience_cp, dict)
    ):
        return {
            "governance_validation_status": "invalid_input",
            "validated_phase": None,
            "governance_complete": False,
        }

    if policy_audit.get("policy_audit_status") == "failed":
        return {
            "governance_validation_status": "failed",
            "validated_phase": None,
            "governance_complete": False,
        }

    if (
        policy_audit.get("policy_audit_status") == "passed"
        and sla.get("sla_status") in ("met", "at_risk")
        and resilience_cp.get("resilience_cp_status") == "operational"
    ):
        return {
            "governance_validation_status": "valid",
            "validated_phase": resilience_cp.get("resilience_phase"),
            "governance_complete": True,
        }

    if policy_audit.get("policy_audit_status") == "passed":
        return {
            "governance_validation_status": "partial",
            "validated_phase": None,
            "governance_complete": False,
        }

    return {
        "governance_validation_status": "invalid_input",
        "validated_phase": None,
        "governance_complete": False,
    }
