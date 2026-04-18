from typing import Any
def validate_command_receipt(validation):
    if not isinstance(validation, dict): return {"op_receipt_validation_status": "invalid"}
    if validation.get("op_receipt_catalog_status") != "cataloged": return {"op_receipt_validation_status": "invalid"}
    return {"op_receipt_validation_status": "valid", "command_id": validation.get("command_id")}
