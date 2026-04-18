from typing import Any
def audit_terminal_aggregate(audit_input):
    if not isinstance(audit_input, dict): return {"op_terminal_aggregate_audit_status": "invalid"}
    if "audit_id" not in audit_input: return {"op_terminal_aggregate_audit_status": "invalid"}
    return {"op_terminal_aggregate_audit_status": "audited", "audit_id": audit_input.get("audit_id")}
