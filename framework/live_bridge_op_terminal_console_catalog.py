from typing import Any
def catalog_console(validation):
    if not isinstance(validation, dict):
        return {"op_console_catalog_status": "invalid"}
    if validation.get("op_console_validation_status") != "valid":
        return {"op_console_catalog_status": "invalid"}
    return {"op_console_catalog_status": "cataloged", "console_count": 1}
