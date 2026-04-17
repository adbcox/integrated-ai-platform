from typing import Any
def normalize_envelope(operation: dict[str, Any], envelope_schema: dict[str, Any], normalize_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(operation, dict) or not isinstance(envelope_schema, dict) or not isinstance(normalize_config, dict):
        return {"envelope_normalization_status": "invalid_input", "envelope_operation_id": None, "envelope_schema_id": None}
    op_ok = operation.get("operation_reception_status") == "received"
    if op_ok:
        return {"envelope_normalization_status": "normalized", "envelope_operation_id": operation.get("received_operation_id"), "envelope_schema_id": envelope_schema.get("schema_id", "env-0001")}
    return {"envelope_normalization_status": "no_operation", "envelope_operation_id": None, "envelope_schema_id": None}
