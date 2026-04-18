from typing import Any
def open_command_channel(channel_input):
    if not isinstance(channel_input, dict): return {"op_command_channel_open_status": "invalid"}
    if "channel_id" not in channel_input: return {"op_command_channel_open_status": "invalid"}
    return {"op_command_channel_open_status": "opened", "channel_id": channel_input.get("channel_id")}
