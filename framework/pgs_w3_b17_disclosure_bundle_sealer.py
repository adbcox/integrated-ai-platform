from typing import Any

def b17_disclosure_bundle_sealer(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"disclosure_bundle_seal_status": "invalid_input"}
    # HARD GATE: upstream seal
    if input_dict.get("pgs_int1_aggregate_proof_seal_status") != "sealed":
        return {"disclosure_bundle_seal_status": "upstream_not_sealed"}
    return {"disclosure_bundle_seal_status": "ok"}
