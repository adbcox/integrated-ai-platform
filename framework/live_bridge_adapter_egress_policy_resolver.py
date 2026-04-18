from typing import Any

def resolve_egress_policy(boundary_policy: Any, catalog: Any, policy_config: Any) -> dict[str, Any]:
    if not isinstance(boundary_policy, dict) or not isinstance(catalog, dict):
        return {"egress_policy_resolution_status": "invalid_input"}
    b_ok = boundary_policy.get("boundary_policy_status") == "resolved"
    c_ok = catalog.get("adapter_catalog_status") == "cataloged"
    if not b_ok or not c_ok:
        return {"egress_policy_resolution_status": "invalid_input"}
    return {
        "egress_policy_resolution_status": "resolved",
        "adapter_id": catalog.get("adapter_id"),
        "policy_constraints_count": 1,
    }
