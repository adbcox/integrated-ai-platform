from typing import Any
def report_exit_ingress(report_input):
    if not isinstance(report_input, dict): return {"exit_ingress_report_status": "invalid"}
    if report_input.get("exit_ingress_validation_status") != "valid": return {"exit_ingress_report_status": "invalid"}
    return {"exit_ingress_report_status": "reported", "audit_id": report_input.get("audit_id")}
