from typing import Any


def validate_learning(
    audit: dict[str, Any],
    autonomy_cp: dict[str, Any],
    observability_cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(audit, dict)
        or not isinstance(autonomy_cp, dict)
        or not isinstance(observability_cp, dict)
    ):
        return {
            "learning_validation_status": "invalid_input",
            "validated_phase": None,
            "learning_complete": False,
        }

    audit_passed = audit.get("learning_audit_status") == "passed"
    aut_op = autonomy_cp.get("autonomy_cp_status") == "operational"
    obs_op = observability_cp.get("observability_cp_status") == "operational"

    if audit_passed and aut_op and obs_op:
        return {
            "learning_validation_status": "valid",
            "validated_phase": autonomy_cp.get("autonomy_phase"),
            "learning_complete": True,
        }

    if audit_passed and (aut_op != obs_op):
        return {
            "learning_validation_status": "partial",
            "validated_phase": None,
            "learning_complete": False,
        }

    if audit.get("learning_audit_status") == "failed":
        return {
            "learning_validation_status": "failed",
            "validated_phase": None,
            "learning_complete": False,
        }

    return {
        "learning_validation_status": "invalid_input",
        "validated_phase": None,
        "learning_complete": False,
    }
