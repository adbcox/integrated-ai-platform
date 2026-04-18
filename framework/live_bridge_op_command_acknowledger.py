from typing import Any
def acknowledge_command(ack_input):
    if not isinstance(ack_input, dict): return {"op_command_ack_status": "invalid"}
    if "ack_id" not in ack_input: return {"op_command_ack_status": "invalid"}
    return {"op_command_ack_status": "acknowledged", "ack_id": ack_input.get("ack_id")}
