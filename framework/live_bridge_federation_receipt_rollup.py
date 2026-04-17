from typing import Any

def rollup_receipts(receipt_aggregation: dict[str, Any], merge: dict[str, Any], fed_ledger: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt_aggregation, dict) or not isinstance(merge, dict) or not isinstance(fed_ledger, dict):
        return {"fed_receipt_rollup_status": "invalid_input"}
    r_ok = receipt_aggregation.get("receipt_aggregation_status") == "aggregated"
    m_ok = merge.get("merge_status") == "merged"
    l_ok = fed_ledger.get("fed_ledger_status") == "written"
    all_complete = r_ok and m_ok and l_ok
    return {"fed_receipt_rollup_status": "rolled_up"} if all_complete else {"fed_receipt_rollup_status": "prerequisites_failed"}

