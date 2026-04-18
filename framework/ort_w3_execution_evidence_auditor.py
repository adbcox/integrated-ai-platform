from typing import Any

def execution_evidence_auditor(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"execution_evidence_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal verification failed
            return {"execution_evidence_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            # HARD GATE: Validation context missing
            return {"execution_evidence_status": "validation_context_failed"}
    return {"execution_evidence_status": "ok"}
