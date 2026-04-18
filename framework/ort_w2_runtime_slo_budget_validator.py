from typing import Any

def runtime_slo_budget_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_budget_validator_status": "invalid"}
    return {"runtime_slo_budget_validator_status": "ok"}
