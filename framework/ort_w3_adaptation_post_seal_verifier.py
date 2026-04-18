from typing import Any

def adaptation_post_seal_verifier(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"adaptation_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal verification failed
            return {"adaptation_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            # HARD GATE: Validation context missing
            return {"adaptation_status": "validation_context_failed"}
    return {"adaptation_status": "ok"}
