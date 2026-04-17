from typing import Any


def validate_adaptation(
    optimization_audit: dict[str, Any],
    governance_cp: dict[str, Any],
    observability_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(optimization_audit, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(observability_cp, dict)
    ):
        return {
            "adaptation_validation_status": "invalid_input",
            "validated_phase": None,
            "adaptation_complete": False,
        }

    audit_passed = optimization_audit.get("optimization_audit_status") == "passed"
    gov_op = governance_cp.get("governance_cp_status") == "operational"
    obs_op = observability_cp.get("observability_cp_status") == "operational"

    if audit_passed and gov_op and obs_op:
        return {
            "adaptation_validation_status": "valid",
            "validated_phase": governance_cp.get("governance_phase"),
            "adaptation_complete": True,
        }

    if audit_passed and (gov_op != obs_op):
        return {
            "adaptation_validation_status": "partial",
            "validated_phase": None,
            "adaptation_complete": False,
        }

    if optimization_audit.get("optimization_audit_status") == "failed":
        return {
            "adaptation_validation_status": "failed",
            "validated_phase": None,
            "adaptation_complete": False,
        }

    return {
        "adaptation_validation_status": "invalid_input",
        "validated_phase": None,
        "adaptation_complete": False,
    }
