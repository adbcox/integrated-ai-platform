from typing import Any

def ingress_backpressure_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_backpressure_status": "invalid"}
    return {"ingress_backpressure_status": "controlled"}
