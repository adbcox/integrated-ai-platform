from typing import Any
def build_command_receipt(receipt_input):
    if not isinstance(receipt_input, dict): return {"op_receipt_build_status": "invalid"}
    if "command_id" not in receipt_input: return {"op_receipt_build_status": "invalid"}
    return {"op_receipt_build_status": "built", "command_id": receipt_input.get("command_id")}
