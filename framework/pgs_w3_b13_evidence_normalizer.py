from typing import Any

def b13_evidence_normalizer(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"pgs_w3_b13_evidence_normalizer_status": "invalid_input"}
    # HARD GATE: upstream seal validation
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"pgs_w3_b13_evidence_normalizer_status": "ok"}
