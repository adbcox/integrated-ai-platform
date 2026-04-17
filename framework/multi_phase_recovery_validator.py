from typing import Any


def validate_recovery_complete(
    audit: dict[str, Any],
    state_restore: dict[str, Any],
    cp: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(audit, dict)
        or not isinstance(state_restore, dict)
        or not isinstance(cp, dict)
    ):
        return {
            "validation_status": "invalid_input",
            "validated_phase": None,
            "recovery_complete": False,
        }

    if audit.get("audit_status") == "failed":
        return {
            "validation_status": "audit_failed",
            "validated_phase": None,
            "recovery_complete": False,
        }

    if (
        audit.get("audit_status") == "passed"
        and state_restore.get("restoration_status") == "restored"
        and cp.get("control_plane_status") == "operational"
    ):
        return {
            "validation_status": "valid",
            "validated_phase": cp.get("active_phase"),
            "recovery_complete": True,
        }

    if audit.get("audit_status") == "passed":
        return {
            "validation_status": "incomplete",
            "validated_phase": None,
            "recovery_complete": False,
        }

    return {
        "validation_status": "invalid_input",
        "validated_phase": None,
        "recovery_complete": False,
    }
