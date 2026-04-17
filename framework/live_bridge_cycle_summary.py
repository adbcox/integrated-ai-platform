from typing import Any

def summarize_cycle(cycle_cp: dict[str, Any], throughput: dict[str, Any], latency: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_cp, dict) or not isinstance(throughput, dict) or not isinstance(latency, dict):
        return {"cycle_summary_status": "invalid_input", "summary_env_id": None, "cycle_health": "pending"}
    cp_op = cycle_cp.get("cycle_cp_status") == "operational"
    tp_ok = throughput.get("throughput_status") == "measured"
    lat_ok = latency.get("latency_status") == "measured"
    if cp_op and tp_ok and lat_ok:
        return {"cycle_summary_status": "complete", "summary_env_id": cycle_cp.get("cycle_cp_env_id"), "cycle_health": "live"}
    if cp_op and (not tp_ok or not lat_ok):
        return {"cycle_summary_status": "partial", "summary_env_id": None, "cycle_health": "pending"}
    return {"cycle_summary_status": "failed", "summary_env_id": None, "cycle_health": "pending"}
