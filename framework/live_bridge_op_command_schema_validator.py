from typing import Any
def validate_command_schema(validation):
    if not isinstance(validation, dict): return {"op_schema_validation_status": "invalid"}
    if validation.get("op_schema_registration_status") != "registered": return {"op_schema_validation_status": "invalid"}
    return {"op_schema_validation_status": "valid", "schema_id": validation.get("schema_id")}
