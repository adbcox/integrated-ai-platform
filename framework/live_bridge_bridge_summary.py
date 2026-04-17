from typing import Any
def summarize_bridge(bridge_cp: dict[str, Any], channel_rollup: dict[str, Any], environment_rollup: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_cp, dict) or not isinstance(channel_rollup, dict) or not isinstance(environment_rollup, dict):
        return {"bridge_summary_status": "invalid_input", "summary_env_id": None, "bridge_health": None}
    cp_ok = bridge_cp.get("bridge_cp_status") == "operational"
    cr_ok = channel_rollup.get("channel_rollup_status") == "rolled_up"
    er_ok = environment_rollup.get("environment_rollup_status") == "rolled_up"
    if cp_ok and cr_ok and er_ok:
        return {"bridge_summary_status": "complete", "summary_env_id": bridge_cp.get("bridge_cp_env_id"), "bridge_health": "live"}
    if cp_ok and (not cr_ok or not er_ok):
        return {"bridge_summary_status": "partial", "summary_env_id": None, "bridge_health": None}
    return {"bridge_summary_status": "failed", "summary_env_id": None, "bridge_health": None}
