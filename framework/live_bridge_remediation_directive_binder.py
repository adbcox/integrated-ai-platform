from typing import Any

def bind_remediation_directive(remediation_plan: Any, directive_config: Any) -> dict[str, Any]:
    if not isinstance(remediation_plan, dict):
        return {"remediation_directive_binding_status": "not_bound"}
    plan_ok = remediation_plan.get("remediation_plan_status") == "planned"
    if not plan_ok:
        return {"remediation_directive_binding_status": "not_bound"}
    return {
        "remediation_directive_binding_status": "bound",
        "directive_id": directive_config.get("directive_id", "DIR_0"),
    }
