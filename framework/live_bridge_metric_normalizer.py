from typing import Any

def normalize_metric(metric_collection: Any, normalization_config: Any) -> dict[str, Any]:
    if not isinstance(metric_collection, dict):
        return {"metric_normalization_status": "not_normalized"}
    coll_ok = metric_collection.get("metric_collection_status") == "collected"
    if not coll_ok:
        return {"metric_normalization_status": "not_normalized"}
    return {
        "metric_normalization_status": "normalized",
        "normalized_value": 0.0,
    }
