from typing import Any

def summarize_federation(fed_cp: dict[str, Any], fed_peer_rollup: dict[str, Any], fed_receipt_rollup: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_cp, dict) or not isinstance(fed_peer_rollup, dict) or not isinstance(fed_receipt_rollup, dict):
        return {"fed_summary_status": "invalid_input"}
    c_ok = fed_cp.get("fed_cp_status") == "operational"
    p_ok = fed_peer_rollup.get("fed_peer_rollup_status") == "rolled_up"
    r_ok = fed_receipt_rollup.get("fed_receipt_rollup_status") == "rolled_up"
    if not c_ok:
        return {"fed_summary_status": "cp_not_operational"}
    return {"fed_summary_status": "complete"} if c_ok and p_ok and r_ok else {"fed_summary_status": "rollups_incomplete"}

