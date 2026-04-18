from typing import Any
def register_exit_schema(schema_input):
    if not isinstance(schema_input, dict): return {"exit_schema_registration_status": "invalid"}
    if "schema_id" not in schema_input: return {"exit_schema_registration_status": "invalid"}
    return {"exit_schema_registration_status": "registered", "schema_id": schema_input.get("schema_id")}
