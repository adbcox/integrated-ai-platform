from typing import Any

def report_governed_federation_completion(finalization: dict, fed_gov_summary: dict, phase_id: str) -> dict:
    if not isinstance(finalization, dict) or not isinstance(fed_gov_summary, dict) or not isinstance(phase_id, str):
        return {"governed_fed_completion_report_status": "invalid_input"}
    ff_ok = finalization.get("governed_fed_finalization_status") == "finalized"
    fs_ok = fed_gov_summary.get("fed_gov_summary_status") == "complete"
    if ff_ok and fs_ok and phase_id:
        return {
            "governed_fed_completion_report_status": "complete",
            "report_phase": phase_id,
            "governed_fed_operating_status": "governed_federation_live",
        }
    if phase_id and (ff_ok or fs_ok):
        return {"governed_fed_completion_report_status": "incomplete"}
    return {"governed_fed_completion_report_status": "invalid_input"}
