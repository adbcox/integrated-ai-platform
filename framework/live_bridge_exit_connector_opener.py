from typing import Any
def open_exit_connector(opener_input):
    if not isinstance(opener_input, dict): return {"exit_connector_open_status": "invalid"}
    if "connector_id" not in opener_input: return {"exit_connector_open_status": "invalid"}
    return {"exit_connector_open_status": "opened", "connector_id": opener_input.get("connector_id")}
