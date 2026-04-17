from typing import Any

def finalize_cycle(cycle_summary: dict[str, Any], cycle_cp: dict[str, Any], cycle_report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_summary, dict) or not isinstance(cycle_cp, dict) or not isinstance(cycle_report, dict):
        return {"cycle_finalization_status": "invalid_input", "finalized_env_id": None, "cycle_finalization_complete": False}
    cs_ok = cycle_summary.get("cycle_summary_status") == "complete"
    cp_op = cycle_cp.get("cycle_cp_status") == "operational"
    cr_ok = cycle_report.get("cycle_report_status") == "complete"
    all_ok = cs_ok and cp_op and cr_ok
    any_ok = cs_ok or cp_op or cr_ok
    if all_ok:
        return {"cycle_finalization_status": "finalized", "finalized_env_id": cycle_cp.get("cycle_cp_env_id"), "cycle_finalization_complete": True}
    if any_ok and not all_ok:
        return {"cycle_finalization_status": "pending", "finalized_env_id": None, "cycle_finalization_complete": False}
    return {"cycle_finalization_status": "blocked", "finalized_env_id": None, "cycle_finalization_complete": False}
