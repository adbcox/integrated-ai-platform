from typing import Any

def workload_dispatch_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_dispatch_validator_status": "invalid"}
    return {"workload_dispatch_validator_status": "ok"}
