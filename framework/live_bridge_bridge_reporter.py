from typing import Any
def report_bridge(bridge_validation: dict[str, Any], bridge_audit: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(bridge_validation, dict) or not isinstance(bridge_audit, dict) or not isinstance(phase_id, str) or not phase_id:
        return {"bridge_report_status": "invalid_input", "report_phase": None, "bridge_complete": False}
    bv_ok = bridge_validation.get("bridge_validation_status") == "valid"
    ba_ok = bridge_audit.get("bridge_audit_status") == "passed"
    if bv_ok and ba_ok:
        return {"bridge_report_status": "complete", "report_phase": phase_id, "bridge_complete": bridge_validation.get("bridge_complete", False)}
    return {"bridge_report_status": "incomplete", "report_phase": None, "bridge_complete": False}
