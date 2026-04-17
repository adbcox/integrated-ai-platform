from typing import Any

def report_cycle(cycle_validation: dict[str, Any], cycle_audit: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(cycle_validation, dict) or not isinstance(cycle_audit, dict) or not isinstance(phase_id, str) or not phase_id:
        return {"cycle_report_status": "invalid_input", "report_phase": None, "cycle_complete": False}
    cv_ok = cycle_validation.get("cycle_validation_status") == "valid"
    ca_ok = cycle_audit.get("cycle_audit_status") == "passed"
    if cv_ok and ca_ok:
        return {"cycle_report_status": "complete", "report_phase": phase_id, "cycle_complete": cycle_validation.get("cycle_complete", False)}
    if isinstance(cycle_validation, dict) and isinstance(cycle_audit, dict) and isinstance(phase_id, str) and phase_id and (not cv_ok or not ca_ok):
        return {"cycle_report_status": "incomplete", "report_phase": None, "cycle_complete": False}
    return {"cycle_report_status": "invalid_input", "report_phase": None, "cycle_complete": False}
