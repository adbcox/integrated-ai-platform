from typing import Any
def describe_exit_channel(descriptor_input):
    if not isinstance(descriptor_input, dict): return {"exit_channel_descriptor_status": "invalid"}
    if "channel_id" not in descriptor_input or "channel_kind" not in descriptor_input: return {"exit_channel_descriptor_status": "invalid"}
    return {"exit_channel_descriptor_status": "described", "channel_id": descriptor_input.get("channel_id")}
