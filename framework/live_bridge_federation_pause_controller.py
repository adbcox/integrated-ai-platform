from typing import Any

def pause_federation(fed_anomaly: dict[str, Any], fed_cp: dict[str, Any], pause_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_anomaly, dict) or not isinstance(fed_cp, dict) or not isinstance(pause_config, dict):
        return {"fed_pause_status": "invalid_input"}
    a_ok = fed_anomaly.get("fed_anomaly_status") == "detected"
    c_ok = fed_cp.get("fed_cp_status") == "operational"
    if not a_ok:
        return {"fed_pause_status": "no_anomaly"}
    return {"fed_pause_status": "paused"} if a_ok and c_ok else {"fed_pause_status": "cp_not_operational"}

