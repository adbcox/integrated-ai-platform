from typing import Any
def register_exit_channel_kind(registrar_input):
    if not isinstance(registrar_input, dict): return {"exit_channel_kind_registration_status": "invalid"}
    if "kind_id" not in registrar_input: return {"exit_channel_kind_registration_status": "invalid"}
    return {"exit_channel_kind_registration_status": "registered", "kind_id": registrar_input.get("kind_id")}
