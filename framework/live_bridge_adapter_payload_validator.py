from typing import Any

def validate_payload(encoding: Any, schema: Any, validator_config: Any) -> dict[str, Any]:
    if not isinstance(encoding, dict) or not isinstance(schema, dict):
        return {"payload_validation_status": "invalid_input"}
    e_ok = encoding.get("payload_encoding_status") == "encoded"
    s_ok = schema.get("payload_schema_registration_status") == "registered"
    if not e_ok or not s_ok:
        return {"payload_validation_status": "invalid_input"}
    return {
        "payload_validation_status": "valid",
        "schema_id": schema.get("schema_id"),
        "encoding_status": "encoded",
    }
