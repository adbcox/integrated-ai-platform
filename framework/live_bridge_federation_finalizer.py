from typing import Any

def finalize_federation(fed_stability_gate: dict[str, Any], fed_cp: dict[str, Any], fed_report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_stability_gate, dict) or not isinstance(fed_cp, dict) or not isinstance(fed_report, dict):
        return {"fed_finalization_status": "invalid_input"}
    s_ok = fed_stability_gate.get("fed_stability_gate_status") == "stable"
    c_ok = fed_cp.get("fed_cp_status") == "operational"
    r_ok = fed_report.get("fed_report_status") == "complete"
    all_ok = s_ok and c_ok and r_ok
    return {"fed_finalization_status": "finalized"} if all_ok else {"fed_finalization_status": "prerequisites_failed"}

