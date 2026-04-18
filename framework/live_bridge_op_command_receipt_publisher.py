from typing import Any
def publish_command_receipt(publisher_input):
    if not isinstance(publisher_input, dict): return {"op_receipt_publication_status": "invalid"}
    if publisher_input.get("op_receipt_sign_status") != "signed": return {"op_receipt_publication_status": "invalid"}
    return {"op_receipt_publication_status": "published", "command_id": publisher_input.get("command_id")}
