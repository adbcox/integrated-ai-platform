from typing import Any

def workload_scope_resolver(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_scope_resolver_status": "invalid"}
    return {"workload_scope_resolver_status": "ok"}
