from typing import Any

def encode_payload(schema: Any, payload: Any, encoder_config: Any) -> dict[str, Any]:
    if not isinstance(schema, dict) or not isinstance(payload, dict):
        return {"payload_encoding_status": "invalid_input"}
    s_ok = schema.get("payload_schema_registration_status") == "registered"
    if not s_ok:
        return {"payload_encoding_status": "invalid_input"}
    return {
        "payload_encoding_status": "encoded",
        "schema_id": schema.get("schema_id"),
        "payload_size_bytes": len(str(payload)),
    }
