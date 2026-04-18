from typing import Any
def report_supervisory_session(report_input):
    if not isinstance(report_input, dict): return {"op_supervisory_session_report_status": "invalid"}
    if report_input.get("op_supervisory_session_validation_status") != "valid": return {"op_supervisory_session_report_status": "invalid"}
    return {"op_supervisory_session_report_status": "reported", "audit_id": report_input.get("audit_id")}
