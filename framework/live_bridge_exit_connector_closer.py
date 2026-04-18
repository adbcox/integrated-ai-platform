from typing import Any
def close_exit_connector(closer_input):
    if not isinstance(closer_input, dict): return {"exit_connector_close_status": "invalid"}
    if "connector_id" not in closer_input: return {"exit_connector_close_status": "invalid"}
    return {"exit_connector_close_status": "closed", "connector_id": closer_input.get("connector_id")}
