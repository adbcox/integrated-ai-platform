from typing import Any
def catalog_command_receipt(catalog_input):
    if not isinstance(catalog_input, dict): return {"op_receipt_catalog_status": "invalid"}
    if catalog_input.get("op_receipt_publication_status") != "published": return {"op_receipt_catalog_status": "invalid"}
    return {"op_receipt_catalog_status": "cataloged", "command_id": catalog_input.get("command_id")}
