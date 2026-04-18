from typing import Any
def report_audit(report_input):
    if not isinstance(report_input, dict): return {"op_audit_report_status": "invalid"}
    if report_input.get("op_audit_validation_status") != "valid": return {"op_audit_report_status": "invalid"}
    return {"op_audit_report_status": "reported", "audit_id": report_input.get("audit_id")}
