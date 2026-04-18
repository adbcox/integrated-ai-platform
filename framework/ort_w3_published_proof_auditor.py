from typing import Any

def published_proof_auditor(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"published_proof_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal verification failed
            return {"published_proof_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            # HARD GATE: Validation context missing
            return {"published_proof_status": "validation_context_failed"}
    return {"published_proof_status": "ok"}
