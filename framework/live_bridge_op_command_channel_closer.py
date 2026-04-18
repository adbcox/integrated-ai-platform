from typing import Any
def close_command_channel(closer_input):
    if not isinstance(closer_input, dict): return {"op_command_channel_close_status": "invalid"}
    if "channel_id" not in closer_input: return {"op_command_channel_close_status": "invalid"}
    return {"op_command_channel_close_status": "closed", "channel_id": closer_input.get("channel_id")}
