from typing import Any
def write_audit_ledger(ledger_input):
    if not isinstance(ledger_input, dict): return {"op_audit_ledger_write_status": "invalid"}
    if "ledger_id" not in ledger_input: return {"op_audit_ledger_write_status": "invalid"}
    return {"op_audit_ledger_write_status": "written", "ledger_id": ledger_input.get("ledger_id")}
