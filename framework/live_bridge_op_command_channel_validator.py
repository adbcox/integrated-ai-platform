from typing import Any
def validate_command_channel(validation):
    if not isinstance(validation, dict): return {"op_command_channel_validation_status": "invalid"}
    if validation.get("op_command_channel_open_status") != "opened": return {"op_command_channel_validation_status": "invalid"}
    return {"op_command_channel_validation_status": "valid", "channel_id": validation.get("channel_id")}
