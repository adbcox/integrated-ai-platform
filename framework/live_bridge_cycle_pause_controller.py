from typing import Any

def pause_cycle(anomaly: dict[str, Any], bridge_cp: dict[str, Any], pause_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(anomaly, dict) or not isinstance(bridge_cp, dict) or not isinstance(pause_config, dict):
        return {"pause_status": "invalid_input", "paused_env_id": None, "pause_reason": None}
    an_detected = anomaly.get("anomaly_status") == "detected"
    cp_op = bridge_cp.get("bridge_cp_status") == "operational"
    if not an_detected:
        return {"pause_status": "no_anomaly", "paused_env_id": None, "pause_reason": None}
    if an_detected and not cp_op:
        return {"pause_status": "bridge_offline", "paused_env_id": None, "pause_reason": None}
    return {"pause_status": "paused", "paused_env_id": bridge_cp.get("bridge_cp_env_id"), "pause_reason": anomaly.get("anomaly_kind")} if an_detected and cp_op else {"pause_status": "invalid_input", "paused_env_id": None, "pause_reason": None}
