from typing import Any

def b18_regulator_handshake_sealer(input_dict):
    # HARD GATE: type check
    if not isinstance(input_dict, dict):
        return {"regulator_handshake_seal_status": "invalid_input"}
    # HARD GATE: upstream seal
    if input_dict.get("disclosure_bundle_seal_status") != "sealed":
        return {"regulator_handshake_seal_status": "upstream_not_sealed"}
    # HARD GATE: upstream seal
    if input_dict.get("pgs_int1_aggregate_proof_seal_status") != "sealed":
        return {"regulator_handshake_seal_status": "upstream_not_sealed"}
    return {"regulator_handshake_seal_status": "ok"}
