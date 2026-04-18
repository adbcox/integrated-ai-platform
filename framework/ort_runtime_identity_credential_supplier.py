from typing import Any

def identity_credential_supplier(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_credential_supply_status": "invalid"}
    return {"identity_credential_supply_status": "supplied"}
