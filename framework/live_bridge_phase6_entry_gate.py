from typing import Any
def gate_phase6_entry(bridge_summary: dict[str, Any], bridge_health: dict[str, Any], capstone_closure: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_summary, dict) or not isinstance(bridge_health, dict) or not isinstance(capstone_closure, dict):
        return {"phase6_entry_gate_status": "invalid_input", "gate_env_id": None, "active_signals": 0}
    bs_ok = bridge_summary.get("bridge_summary_status") == "complete"
    bh_ok = bridge_health.get("bridge_health_status") == "healthy"
    cc_ok = capstone_closure.get("capstone_closure_report_status") == "complete"
    all_ok = bs_ok and bh_ok and cc_ok
    any_ok = bs_ok or bh_ok or cc_ok
    if all_ok:
        return {"phase6_entry_gate_status": "open", "gate_env_id": bridge_summary.get("summary_env_id"), "active_signals": 3}
    if any_ok:
        return {"phase6_entry_gate_status": "partial", "gate_env_id": None, "active_signals": sum([bs_ok, bh_ok, cc_ok])}
    return {"phase6_entry_gate_status": "closed", "gate_env_id": None, "active_signals": 0}
