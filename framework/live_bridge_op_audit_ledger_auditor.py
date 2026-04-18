from typing import Any
def audit_audit_ledger(audit_input):
    if not isinstance(audit_input, dict): return {"op_audit_ledger_audit_status": "invalid"}
    if audit_input.get("op_audit_ledger_write_status") != "written": return {"op_audit_ledger_audit_status": "invalid"}
    return {"op_audit_ledger_audit_status": "audited", "ledger_id": audit_input.get("ledger_id")}
