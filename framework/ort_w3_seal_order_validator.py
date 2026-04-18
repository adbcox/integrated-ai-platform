from typing import Any

def seal_order_validator(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"seal_order_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal verification failed
            return {"seal_order_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            # HARD GATE: Validation context missing
            return {"seal_order_validator_status": "validation_context_failed"}
    return {"seal_order_validator_status": "ok"}
