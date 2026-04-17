from typing import Any
def finalize_phase6_entry(readiness: dict[str, Any], bridge_cp: dict[str, Any], bridge_summary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(readiness, dict) or not isinstance(bridge_cp, dict) or not isinstance(bridge_summary, dict):
        return {"phase6_entry_finalization_status": "invalid_input", "finalized_env_id": None, "phase6_entry_complete": False}
    r_ok = readiness.get("phase6_readiness_status") == "ready"
    cp_ok = bridge_cp.get("bridge_cp_status") == "operational"
    bs_ok = bridge_summary.get("bridge_summary_status") == "complete"
    all_ok = r_ok and cp_ok and bs_ok
    any_ok = r_ok or cp_ok or bs_ok
    if all_ok:
        return {"phase6_entry_finalization_status": "finalized", "finalized_env_id": readiness.get("ready_env_id"), "phase6_entry_complete": True}
    if any_ok:
        return {"phase6_entry_finalization_status": "pending", "finalized_env_id": None, "phase6_entry_complete": False}
    return {"phase6_entry_finalization_status": "blocked", "finalized_env_id": None, "phase6_entry_complete": False}
