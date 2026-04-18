from typing import Any

def ingress_rate_limiter(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_rate_limit_status": "invalid"}
    return {"ingress_rate_limit_status": "limited"}
