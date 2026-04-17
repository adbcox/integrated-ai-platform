from typing import Any

def resolve_conflict(conflict: dict[str, Any], governance_cp: dict[str, Any], resolver_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(conflict, dict) or not isinstance(governance_cp, dict) or not isinstance(resolver_config, dict):
        return {"resolution_status": "invalid_input"}
    c_ok = conflict.get("conflict_status") == "detected"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if c_ok and not g_ok:
        return {"resolution_status": "governance_offline"}
    if conflict.get("conflict_status") == "none":
        return {"resolution_status": "no_conflict"}
    return {"resolution_status": "resolved"} if c_ok and g_ok else {"resolution_status": "cannot_resolve"}

