from typing import Any

def b2_publication_attestation_registrar(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"pgs_w3_b2_publication_attestation_registrar_status": "invalid_input"}
    # HARD GATE: upstream seal validation
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"pgs_w3_b2_publication_attestation_registrar_status": "ok"}
