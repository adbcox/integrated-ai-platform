from typing import Any
def report_command_reconciliation(report_input):
    if not isinstance(report_input, dict): return {"op_reconciliation_report_status": "invalid"}
    if report_input.get("op_reconciliation_validation_status") != "valid": return {"op_reconciliation_report_status": "invalid"}
    return {"op_reconciliation_report_status": "reported", "reconciliation_id": report_input.get("reconciliation_id")}
