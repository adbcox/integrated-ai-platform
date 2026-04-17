from typing import Any

def report_federation(fed_validation: dict[str, Any], fed_audit: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(fed_validation, dict) or not isinstance(fed_audit, dict) or not isinstance(phase_id, str):
        return {"fed_report_status": "invalid_input"}
    v_ok = fed_validation.get("fed_validation_status") == "valid"
    a_ok = fed_audit.get("fed_audit_status") == "passed"
    if not v_ok:
        return {"fed_report_status": "validation_failed"}
    return {"fed_report_status": "complete"} if v_ok and a_ok else {"fed_report_status": "audit_failed"}

