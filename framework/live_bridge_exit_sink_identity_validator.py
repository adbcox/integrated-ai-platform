from typing import Any
def validate_exit_sink_identity(validation):
    if not isinstance(validation, dict): return {"exit_sink_identity_validation_status": "invalid"}
    if "sink_operator_id" not in validation: return {"exit_sink_identity_validation_status": "invalid"}
    return {"exit_sink_identity_validation_status": "valid", "sink_operator_id": validation.get("sink_operator_id")}
