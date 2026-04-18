from typing import Any

def collect_metric(metric_schema: Any, measurement_data: Any) -> dict[str, Any]:
    if not isinstance(metric_schema, dict) or not isinstance(measurement_data, dict):
        return {"metric_collection_status": "not_collected"}
    schema_ok = metric_schema.get("metric_schema_registration_status") == "registered"
    if not schema_ok:
        return {"metric_collection_status": "not_collected"}
    return {
        "metric_collection_status": "collected",
        "sample_count": measurement_data.get("sample_count", 0),
    }
