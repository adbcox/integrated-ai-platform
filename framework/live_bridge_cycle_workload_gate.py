from typing import Any

def gate_workload(bridge_health: dict[str, Any], backpressure: dict[str, Any], quota_tracker: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_health, dict) or not isinstance(backpressure, dict) or not isinstance(quota_tracker, dict):
        return {"workload_gate_status": "invalid_input", "gate_signals": 0, "gate_reason": "invalid"}
    h_ok = bridge_health.get("bridge_health_status") == "healthy"
    bp_ok = backpressure.get("backpressure_status") == "normal"
    q_ok = quota_tracker.get("quota_tracker_status") == "under_limit"
    all_ok = h_ok and bp_ok and q_ok
    any_ok = h_ok or bp_ok or q_ok
    if all_ok:
        return {"workload_gate_status": "open", "gate_signals": 3, "gate_reason": "healthy_and_metered"}
    if any_ok and not all_ok:
        return {"workload_gate_status": "partial", "gate_signals": sum([h_ok, bp_ok, q_ok]), "gate_reason": "pressure_or_quota"}
    return {"workload_gate_status": "closed", "gate_signals": 0, "gate_reason": "pressure_or_quota"}
