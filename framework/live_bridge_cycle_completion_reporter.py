from typing import Any

def report_cycle_completion(cycle_finalization: dict[str, Any], cycle_summary: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(cycle_finalization, dict) or not isinstance(cycle_summary, dict) or not isinstance(phase_id, str) or not phase_id:
        return {"cycle_completion_report_status": "invalid_input", "report_phase": None, "cycle_operating_status": "pending"}
    cf_ok = cycle_finalization.get("cycle_finalization_status") == "finalized"
    cs_ok = cycle_summary.get("cycle_summary_status") == "complete"
    if cf_ok and cs_ok:
        return {"cycle_completion_report_status": "complete", "report_phase": phase_id, "cycle_operating_status": "live_operating"}
    if isinstance(cycle_finalization, dict) and isinstance(cycle_summary, dict) and isinstance(phase_id, str) and phase_id and (not cf_ok or not cs_ok):
        return {"cycle_completion_report_status": "incomplete", "report_phase": None, "cycle_operating_status": "pending"}
    return {"cycle_completion_report_status": "invalid_input", "report_phase": None, "cycle_operating_status": "pending"}
