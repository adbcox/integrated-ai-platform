from typing import Any

def register_payload_schema(catalog: Any, schema_descriptor: Any, registrar_config: Any) -> dict[str, Any]:
    if not isinstance(catalog, dict) or not isinstance(schema_descriptor, dict):
        return {"payload_schema_registration_status": "invalid_input"}
    c_ok = catalog.get("adapter_catalog_status") == "cataloged"
    if not c_ok:
        return {"payload_schema_registration_status": "invalid_input"}
    schema_id = schema_descriptor.get("schema_id")
    fields = schema_descriptor.get("fields")
    if not schema_id or not fields or not isinstance(fields, list) or len(fields) == 0:
        return {"payload_schema_registration_status": "invalid_input"}
    return {
        "payload_schema_registration_status": "registered",
        "schema_id": schema_id,
        "field_count": len(fields),
    }
