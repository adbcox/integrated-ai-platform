from typing import Any
def enforce_exit_policy(enforcer_input):
    if not isinstance(enforcer_input, dict): return {"exit_policy_enforcement_status": "invalid"}
    if enforcer_input.get("exit_policy_resolve_status") != "resolved": return {"exit_policy_enforcement_status": "invalid"}
    return {"exit_policy_enforcement_status": "enforced", "policy_id": enforcer_input.get("policy_id")}
