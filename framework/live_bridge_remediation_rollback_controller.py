from typing import Any

def control_remediation_rollback(remediation_verification: Any, rollback_config: Any) -> dict[str, Any]:
    if not isinstance(remediation_verification, dict):
        return {"remediation_rollback_control_status": "not_controlled"}
    verify_ok = remediation_verification.get("remediation_verification_status") == "verified"
    if not verify_ok:
        return {"remediation_rollback_control_status": "not_controlled"}
    should_rollback = rollback_config.get("should_rollback", False)
    return {
        "remediation_rollback_control_status": "controlled",
        "rollback_enabled": should_rollback,
    }
