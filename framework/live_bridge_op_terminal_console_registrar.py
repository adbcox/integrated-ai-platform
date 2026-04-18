from typing import Any

def register_console(descriptor):
    if not isinstance(descriptor, dict):
        return {"op_console_registration_status": "invalid"}
    if descriptor.get("op_console_descriptor_status") != "described":
        return {"op_console_registration_status": "invalid"}
    return {"op_console_registration_status": "registered", "console_id": descriptor.get("console_id")}
