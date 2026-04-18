from typing import Any

def family_purity_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"family_purity_auditor_status": "invalid_input"}
    return {"family_purity_auditor_status": "valid"}
