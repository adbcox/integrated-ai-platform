from typing import Any
def bind_exit_directive(binding):
    if not isinstance(binding, dict): return {"exit_directive_bind_status": "invalid"}
    if binding.get("exit_policy_enforcement_status") != "enforced": return {"exit_directive_bind_status": "invalid"}
    return {"exit_directive_bind_status": "bound", "policy_id": binding.get("policy_id")}
