from typing import Any
def build_ingress_channel(policy: dict[str, Any], catalog: dict[str, Any], channel_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(policy, dict) or not isinstance(catalog, dict) or not isinstance(channel_config, dict):
        return {"ingress_channel_status": "invalid_input", "ingress_env_id": None, "ingress_channel_id": None, "ingress_direction": None}
    p_ok = policy.get("boundary_policy_status") == "resolved"
    c_ok = catalog.get("env_catalog_status") == "cataloged"
    if p_ok and c_ok:
        return {"ingress_channel_status": "built", "ingress_env_id": policy.get("policy_env_id"), "ingress_channel_id": channel_config.get("channel_id", "in-0001"), "ingress_direction": "inbound"}
    return {"ingress_channel_status": "no_policy" if not p_ok else "invalid_input", "ingress_env_id": None, "ingress_channel_id": None, "ingress_direction": None}
