from typing import Any
def resolve_boundary_policy(guard: dict[str, Any], governance_cp: dict[str, Any], policy_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(guard, dict) or not isinstance(governance_cp, dict) or not isinstance(policy_config, dict):
        return {"boundary_policy_status": "invalid_input", "policy_env_id": None, "policy_id": None}
    g_ok = guard.get("boundary_guard_status") == "armed"
    gcp_ok = governance_cp.get("governance_cp_status") == "operational"
    if g_ok and gcp_ok:
        return {"boundary_policy_status": "resolved", "policy_env_id": guard.get("guard_env_id"), "policy_id": policy_config.get("policy_id", "pol-0001")}
    return {"boundary_policy_status": "not_armed" if not g_ok else "governance_offline", "policy_env_id": None, "policy_id": None}
