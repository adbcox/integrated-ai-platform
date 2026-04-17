from typing import Any

def audit_operation_ledger(ledger: dict[str, Any], reconciliation: dict[str, Any], auditor_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(ledger, dict) or not isinstance(reconciliation, dict) or not isinstance(auditor_config, dict):
        return {"op_ledger_audit_status": "invalid_input", "audit_operation_id": None, "audit_ok_count": 0}
    l_ok = ledger.get("op_ledger_status") == "written"
    r_ok = reconciliation.get("reconciliation_execution_status") == "executed"
    all_ok = l_ok and r_ok
    any_ok = l_ok or r_ok
    if all_ok:
        return {"op_ledger_audit_status": "passed", "audit_operation_id": ledger.get("ledger_operation_id"), "audit_ok_count": 2}
    if any_ok and not all_ok:
        return {"op_ledger_audit_status": "degraded", "audit_operation_id": None, "audit_ok_count": int(l_ok) + int(r_ok)}
    return {"op_ledger_audit_status": "failed", "audit_operation_id": None, "audit_ok_count": 0}
