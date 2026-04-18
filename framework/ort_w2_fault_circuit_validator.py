from typing import Any

def fault_circuit_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_circuit_validator_status": "invalid"}
    return {"fault_circuit_validator_status": "ok"}
