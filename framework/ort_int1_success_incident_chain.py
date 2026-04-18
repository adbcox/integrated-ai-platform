from typing import Any

def success_incident_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_incident_chain_status": "invalid_input"}
    return {"success_incident_chain_status": "valid"}
