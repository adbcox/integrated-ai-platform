from typing import Any

def deployment_credential_supplier(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_credential_supply_status": "invalid"}
    return {"deployment_credential_supply_status": "supplied"}
