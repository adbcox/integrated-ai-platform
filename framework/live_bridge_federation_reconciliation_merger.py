from typing import Any

def merge_reconciliations(reconciliation: dict[str, Any], receipt_aggregation: dict[str, Any], merger_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(reconciliation, dict) or not isinstance(receipt_aggregation, dict) or not isinstance(merger_config, dict):
        return {"merge_status": "invalid_input", "merge_id": None}
    rec_ok = reconciliation.get("reconciliation_execution_status") == "executed"
    r_ok = receipt_aggregation.get("receipt_aggregation_status") == "aggregated"
    if not rec_ok:
        return {"merge_status": "reconciliation_not_executed", "merge_id": None}
    return {"merge_status": "merged", "merge_id": merger_config.get("merge_id", "mrg-0001")} if rec_ok and r_ok else {"merge_status": "aggregation_failed", "merge_id": None}

