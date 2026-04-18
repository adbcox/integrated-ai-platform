from typing import Any

def ingress_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_report_status": "invalid"}
    return {"ingress_report_status": "reported"}
