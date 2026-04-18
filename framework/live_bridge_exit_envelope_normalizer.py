from typing import Any
def normalize_exit_envelope(normalization):
    if not isinstance(normalization, dict): return {"exit_envelope_normalization_status": "invalid"}
    if normalization.get("exit_envelope_receive_status") != "received": return {"exit_envelope_normalization_status": "invalid"}
    return {"exit_envelope_normalization_status": "normalized", "envelope_id": normalization.get("envelope_id")}
