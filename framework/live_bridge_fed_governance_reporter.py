from typing import Any

def report_fed_governance(fed_gov_validation: dict, fed_gov_audit: dict, phase_id: str) -> dict:
    if not isinstance(fed_gov_validation, dict) or not isinstance(fed_gov_audit, dict) or not isinstance(phase_id, str):
        return {"fed_gov_report_status": "invalid_input"}
    fv_ok = fed_gov_validation.get("fed_gov_validation_status") == "valid"
    fa_ok = fed_gov_audit.get("fed_gov_audit_status") == "passed"
    if fv_ok and fa_ok and phase_id:
        return {
            "fed_gov_report_status": "complete",
            "report_phase": phase_id,
            "fed_gov_complete": fed_gov_validation.get("fed_gov_complete", False),
        }
    if phase_id and (fv_ok or fa_ok):
        return {"fed_gov_report_status": "incomplete"}
    return {"fed_gov_report_status": "invalid_input"}
