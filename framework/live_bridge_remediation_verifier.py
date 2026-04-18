from typing import Any

def verify_remediation(remediation_execution: Any, verification_config: Any) -> dict[str, Any]:
    if not isinstance(remediation_execution, dict):
        return {"remediation_verification_status": "not_verified"}
    exec_ok = remediation_execution.get("remediation_execution_status") == "executed"
    if not exec_ok:
        return {"remediation_verification_status": "not_verified"}
    return {
        "remediation_verification_status": "verified",
        "verification_result": remediation_execution.get("execution_result", "unknown"),
    }
