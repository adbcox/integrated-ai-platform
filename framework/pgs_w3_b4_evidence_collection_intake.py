from typing import Any

def b4_evidence_collection_intake(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"pgs_w3_b4_evidence_collection_intake_status": "invalid_input"}
    # HARD GATE: upstream seal validation
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"pgs_w3_b4_evidence_collection_intake_status": "ok"}
