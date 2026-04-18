from typing import Any

def register_metric_schema(schema_config: Any) -> dict[str, Any]:
    if not isinstance(schema_config, dict):
        return {"metric_schema_registration_status": "not_registered"}
    if not schema_config.get("schema_id"):
        return {"metric_schema_registration_status": "not_registered"}
    fields = schema_config.get("fields", [])
    if not fields:
        return {"metric_schema_registration_status": "not_registered"}
    return {
        "metric_schema_registration_status": "registered",
        "schema_id": schema_config.get("schema_id"),
    }
