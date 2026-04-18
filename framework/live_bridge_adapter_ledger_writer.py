from typing import Any

def write_adapter_ledger(reconciliation: Any, adapter_signature: Any, ledger_config: Any) -> dict[str, Any]:
    if not isinstance(reconciliation, dict) or not isinstance(adapter_signature, dict):
        return {"adapter_ledger_write_status": "failed"}
    r_ok = reconciliation.get("adapter_reconciliation_execution_status") == "executed"
    s_ok = adapter_signature.get("adapter_receipt_signature_status") == "signed"
    if not r_ok or not s_ok:
        return {"adapter_ledger_write_status": "failed"}
    return {
        "adapter_ledger_write_status": "written",
        "adapter_id": reconciliation.get("adapter_id"),
        "entry_count": 1,
    }
