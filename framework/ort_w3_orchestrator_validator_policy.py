from typing import Any

def orchestrator_validator_policy(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"orchestrator_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal verification failed
            return {"orchestrator_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            # HARD GATE: Validation context missing
            return {"orchestrator_validator_status": "validation_context_failed"}
    return {"orchestrator_validator_status": "ok"}
