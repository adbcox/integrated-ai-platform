from typing import Any

def workload_authorizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_authorizer_status": "invalid"}
    return {"workload_authorizer_status": "ok"}
