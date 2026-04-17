from typing import Any
def build_egress_channel(policy: dict[str, Any], catalog: dict[str, Any], channel_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(policy, dict) or not isinstance(catalog, dict) or not isinstance(channel_config, dict):
        return {"egress_channel_status": "invalid_input", "egress_env_id": None, "egress_channel_id": None, "egress_direction": None}
    p_ok = policy.get("boundary_policy_status") == "resolved"
    c_ok = catalog.get("env_catalog_status") == "cataloged"
    if p_ok and c_ok:
        return {"egress_channel_status": "built", "egress_env_id": policy.get("policy_env_id"), "egress_channel_id": channel_config.get("channel_id", "out-0001"), "egress_direction": "outbound"}
    return {"egress_channel_status": "no_policy" if not p_ok else "invalid_input", "egress_env_id": None, "egress_channel_id": None, "egress_direction": None}
