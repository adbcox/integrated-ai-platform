from typing import Any
def encode_exit_payload(encoder_input):
    if not isinstance(encoder_input, dict): return {"exit_payload_encode_status": "invalid"}
    if "payload_id" not in encoder_input: return {"exit_payload_encode_status": "invalid"}
    return {"exit_payload_encode_status": "encoded", "payload_id": encoder_input.get("payload_id")}
