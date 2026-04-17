from typing import Any
def validate_phase6_readiness(entry_gate: dict[str, Any], bridge_cp: dict[str, Any], stack_readiness: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(entry_gate, dict) or not isinstance(bridge_cp, dict) or not isinstance(stack_readiness, dict):
        return {"phase6_readiness_status": "invalid_input", "ready_env_id": None, "active_planes": 0}
    eg_ok = entry_gate.get("phase6_entry_gate_status") == "open"
    cp_ok = bridge_cp.get("bridge_cp_status") == "operational"
    sr_ok = stack_readiness.get("stack_readiness_status") == "ready"
    all_ok = eg_ok and cp_ok and sr_ok
    any_ok = eg_ok or cp_ok or sr_ok
    if all_ok:
        return {"phase6_readiness_status": "ready", "ready_env_id": entry_gate.get("gate_env_id"), "active_planes": stack_readiness.get("active_planes", 0)}
    if any_ok:
        return {"phase6_readiness_status": "partial", "ready_env_id": None, "active_planes": 0}
    return {"phase6_readiness_status": "not_ready", "ready_env_id": None, "active_planes": 0}
