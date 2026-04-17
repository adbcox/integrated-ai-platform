from typing import Any

def aggregate_receipts(receipt_signature: dict[str, Any], collection: dict[str, Any], aggregator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt_signature, dict) or not isinstance(collection, dict) or not isinstance(aggregator_config, dict):
        return {"receipt_aggregation_status": "invalid_input", "aggregated_count": 0}
    r_ok = receipt_signature.get("receipt_signature_status") == "signed"
    c_ok = collection.get("collection_status") == "collected"
    agg_count = collection.get("collected_count", 0) if (r_ok and c_ok) else 0
    return {"receipt_aggregation_status": "aggregated", "aggregated_count": agg_count} if r_ok and c_ok else {"receipt_aggregation_status": "prerequisites_failed", "aggregated_count": 0}

