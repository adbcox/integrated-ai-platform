from typing import Any

def audit_adapter_ledger(ledger: Any, reconciliation: Any, auditor_config: Any) -> dict[str, Any]:
    if not isinstance(ledger, dict) or not isinstance(reconciliation, dict):
        return {"adapter_ledger_audit_status": "failed"}
    l_ok = ledger.get("adapter_ledger_write_status") == "written"
    r_ok = reconciliation.get("adapter_reconciliation_execution_status") == "executed"
    if not l_ok or not r_ok:
        return {"adapter_ledger_audit_status": "failed"}
    return {
        "adapter_ledger_audit_status": "passed",
        "adapter_id": ledger.get("adapter_id"),
    }
