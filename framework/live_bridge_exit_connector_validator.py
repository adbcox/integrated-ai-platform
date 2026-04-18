from typing import Any
def validate_exit_connector(validation):
    if not isinstance(validation, dict): return {"exit_connector_validation_status": "invalid"}
    if validation.get("exit_connector_open_status") != "opened": return {"exit_connector_validation_status": "invalid"}
    return {"exit_connector_validation_status": "valid", "connector_id": validation.get("connector_id")}
