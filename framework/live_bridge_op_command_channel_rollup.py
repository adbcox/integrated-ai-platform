from typing import Any
def rollup_command_channel(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_command_channel_rollup_status": "invalid"}
    if "channel_count" not in rollup_input: return {"op_command_channel_rollup_status": "invalid"}
    return {"op_command_channel_rollup_status": "rolled_up", "channel_count": rollup_input.get("channel_count")}
