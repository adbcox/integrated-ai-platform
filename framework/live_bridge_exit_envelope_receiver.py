from typing import Any
def receive_exit_envelope(envelope_input):
    if not isinstance(envelope_input, dict): return {"exit_envelope_receive_status": "invalid"}
    if "envelope_id" not in envelope_input: return {"exit_envelope_receive_status": "invalid"}
    return {"exit_envelope_receive_status": "received", "envelope_id": envelope_input.get("envelope_id")}
