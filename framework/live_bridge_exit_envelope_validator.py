from typing import Any
def validate_exit_envelope(validation):
    if not isinstance(validation, dict): return {"exit_envelope_validation_status": "invalid"}
    if validation.get("exit_envelope_normalization_status") != "normalized": return {"exit_envelope_validation_status": "invalid"}
    return {"exit_envelope_validation_status": "valid", "envelope_id": validation.get("envelope_id")}
