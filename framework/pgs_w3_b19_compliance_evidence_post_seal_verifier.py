from typing import Any

def b19_compliance_evidence_post_seal_verifier(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"compliance_evidence_post_seal_verification_status": "invalid_input"}
    # HARD GATE: upstream seal validation
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"compliance_evidence_post_seal_verification_status": "ok"}
