from typing import Any

def write_operation_ledger(reconciliation: dict[str, Any], receipt_signature: dict[str, Any], ledger_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(reconciliation, dict) or not isinstance(receipt_signature, dict) or not isinstance(ledger_config, dict):
        return {"op_ledger_status": "invalid_input", "ledger_operation_id": None, "ledger_entry_id": None}
    r_ok = reconciliation.get("reconciliation_execution_status") == "executed"
    rs_ok = receipt_signature.get("receipt_signature_status") == "signed"
    if not r_ok:
        return {"op_ledger_status": "no_reconciliation", "ledger_operation_id": None, "ledger_entry_id": None}
    if r_ok and not rs_ok:
        return {"op_ledger_status": "no_signature", "ledger_operation_id": None, "ledger_entry_id": None}
    return {"op_ledger_status": "written", "ledger_operation_id": reconciliation.get("executed_operation_id"), "ledger_entry_id": ledger_config.get("entry_id", "ope-0001")} if r_ok and rs_ok else {"op_ledger_status": "invalid_input", "ledger_operation_id": None, "ledger_entry_id": None}
