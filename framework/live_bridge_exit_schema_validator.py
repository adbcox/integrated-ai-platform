from typing import Any
def validate_exit_schema(validation):
    if not isinstance(validation, dict): return {"exit_schema_validation_status": "invalid"}
    if validation.get("exit_schema_registration_status") != "registered": return {"exit_schema_validation_status": "invalid"}
    return {"exit_schema_validation_status": "valid", "schema_id": validation.get("schema_id")}
