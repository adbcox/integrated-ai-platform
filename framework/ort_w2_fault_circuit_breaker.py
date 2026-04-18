from typing import Any

def fault_circuit_breaker(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_circuit_breaker_status": "invalid"}
    return {"fault_circuit_breaker_status": "ok"}
