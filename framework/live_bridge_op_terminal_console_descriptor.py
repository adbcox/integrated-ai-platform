from typing import Any

def describe_console(descriptor_input):
    if not isinstance(descriptor_input, dict):
        return {"op_console_descriptor_status": "invalid"}
    if "console_id" not in descriptor_input or "console_kind" not in descriptor_input:
        return {"op_console_descriptor_status": "invalid"}
    cid = descriptor_input.get("console_id")
    ckind = descriptor_input.get("console_kind")
    if not cid or not ckind:
        return {"op_console_descriptor_status": "invalid"}
    return {"op_console_descriptor_status": "described", "console_id": cid, "console_kind": ckind}
