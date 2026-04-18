from typing import Any

def environment_constraint_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_constraint_status": "invalid"}
    return {"environment_constraint_status": "constrained"}
