from typing import Any
def register_command_schema(schema_input):
    if not isinstance(schema_input, dict): return {"op_schema_registration_status": "invalid"}
    if "schema_id" not in schema_input: return {"op_schema_registration_status": "invalid"}
    return {"op_schema_registration_status": "registered", "schema_id": schema_input.get("schema_id")}
