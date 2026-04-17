from typing import Any

def gate_federation_stability(fed_entry_gate: dict[str, Any], fed_cp: dict[str, Any], fed_quota: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_entry_gate, dict) or not isinstance(fed_cp, dict) or not isinstance(fed_quota, dict):
        return {"fed_stability_gate_status": "invalid_input"}
    e_ok = fed_entry_gate.get("fed_entry_gate_status") == "open"
    c_ok = fed_cp.get("fed_cp_status") == "operational"
    q_ok = fed_quota.get("fed_quota_status") == "under_fed_limit"
    all_ok = e_ok and c_ok and q_ok
    return {"fed_stability_gate_status": "stable"} if all_ok else {"fed_stability_gate_status": "unstable"}

