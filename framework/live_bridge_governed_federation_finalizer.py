from typing import Any

def finalize_governed_federation(stability_gate: dict, fed_gov_cp: dict, fed_gov_report: dict) -> dict:
    if not isinstance(stability_gate, dict) or not isinstance(fed_gov_cp, dict) or not isinstance(fed_gov_report, dict):
        return {"governed_fed_finalization_status": "invalid_input"}
    sg_ok = stability_gate.get("governed_fed_stability_gate_status") == "stable"
    cp_op = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    fr_ok = fed_gov_report.get("fed_gov_report_status") == "complete"
    all_ok = sg_ok and cp_op and fr_ok
    any_ok = sg_ok or cp_op or fr_ok
    if all_ok:
        return {
            "governed_fed_finalization_status": "finalized",
            "finalized_env_id": fed_gov_cp.get("fed_gov_cp_env_id"),
            "governed_fed_complete": True,
        }
    if any_ok:
        return {"governed_fed_finalization_status": "pending", "governed_fed_complete": False}
    return {"governed_fed_finalization_status": "blocked", "governed_fed_complete": False}
