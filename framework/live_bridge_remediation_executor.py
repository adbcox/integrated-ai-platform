from typing import Any

def execute_remediation(remediation_directive_binding: Any, fed_gov_cp: Any) -> dict[str, Any]:
    if not isinstance(remediation_directive_binding, dict) or not isinstance(fed_gov_cp, dict):
        return {"remediation_execution_status": "not_executed"}
    bind_ok = remediation_directive_binding.get("remediation_directive_binding_status") == "bound"
    fed_ok = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    if not bind_ok or not fed_ok:
        return {"remediation_execution_status": "not_executed"}
    return {
        "remediation_execution_status": "executed",
        "execution_result": "success",
    }
