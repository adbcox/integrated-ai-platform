from typing import Any
def validate_command_envelope(validation):
    if not isinstance(validation, dict): return {"op_envelope_validation_status": "invalid"}
    if validation.get("op_envelope_normalization_status") != "normalized": return {"op_envelope_validation_status": "invalid"}
    return {"op_envelope_validation_status": "valid", "envelope_id": validation.get("envelope_id")}
