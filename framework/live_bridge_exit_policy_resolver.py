from typing import Any
def resolve_exit_policy(resolver_input):
    if not isinstance(resolver_input, dict): return {"exit_policy_resolve_status": "invalid"}
    if "policy_id" not in resolver_input: return {"exit_policy_resolve_status": "invalid"}
    return {"exit_policy_resolve_status": "resolved", "policy_id": resolver_input.get("policy_id")}
