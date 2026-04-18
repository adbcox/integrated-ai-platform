from typing import Any
def register_exit_channel(registrar_input):
    if not isinstance(registrar_input, dict): return {"exit_channel_registration_status": "invalid"}
    if registrar_input.get("exit_channel_descriptor_status") != "described": return {"exit_channel_registration_status": "invalid"}
    return {"exit_channel_registration_status": "registered", "channel_id": registrar_input.get("channel_id")}
