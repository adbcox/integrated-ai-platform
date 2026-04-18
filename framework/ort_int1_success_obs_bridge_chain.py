from typing import Any

def success_obs_bridge_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_obs_bridge_chain_status": "invalid_input"}
    return {"success_obs_bridge_chain_status": "valid"}
