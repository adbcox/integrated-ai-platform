from typing import Any
def normalize_command_envelope(normalization):
    if not isinstance(normalization, dict): return {"op_envelope_normalization_status": "invalid"}
    if normalization.get("op_envelope_receive_status") != "received": return {"op_envelope_normalization_status": "invalid"}
    return {"op_envelope_normalization_status": "normalized", "envelope_id": normalization.get("envelope_id")}
