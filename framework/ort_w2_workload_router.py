from typing import Any

def workload_router(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_router_status": "invalid"}
    return {"workload_router_status": "ok"}
