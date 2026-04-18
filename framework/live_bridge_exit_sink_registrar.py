from typing import Any
def register_exit_sink(registrar_input):
    if not isinstance(registrar_input, dict): return {"exit_sink_registration_status": "invalid"}
    if registrar_input.get("exit_sink_descriptor_status") != "described": return {"exit_sink_registration_status": "invalid"}
    return {"exit_sink_registration_status": "registered", "sink_id": registrar_input.get("sink_id")}
