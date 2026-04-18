from typing import Any
def sign_command_receipt(signer_input):
    if not isinstance(signer_input, dict): return {"op_receipt_sign_status": "invalid"}
    if signer_input.get("op_receipt_build_status") != "built": return {"op_receipt_sign_status": "invalid"}
    return {"op_receipt_sign_status": "signed", "command_id": signer_input.get("command_id")}
