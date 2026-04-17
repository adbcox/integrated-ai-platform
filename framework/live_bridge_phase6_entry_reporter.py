from typing import Any
def report_phase6_entry(finalization: dict[str, Any], readiness: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(finalization, dict) or not isinstance(readiness, dict) or not isinstance(phase_id, str) or not phase_id:
        return {"phase6_entry_report_status": "invalid_input", "report_phase": None, "phase6_entry_status": None}
    f_ok = finalization.get("phase6_entry_finalization_status") == "finalized"
    r_ok = readiness.get("phase6_readiness_status") == "ready"
    if f_ok and r_ok:
        return {"phase6_entry_report_status": "complete", "report_phase": phase_id, "phase6_entry_status": "live"}
    return {"phase6_entry_report_status": "incomplete", "report_phase": None, "phase6_entry_status": None}
