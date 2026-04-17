from typing import Any

def resolve_authority(identity: dict, authority_claim: dict, resolver_config: dict) -> dict:
    if not isinstance(identity, dict) or not isinstance(authority_claim, dict) or not isinstance(resolver_config, dict):
        return {"authority_resolution_status": "invalid_input"}
    i_ok = identity.get("operator_identity_status") == "valid"
    ac_valid = authority_claim.get("authority_level") in ("observer", "operator", "supervisor", "root")
    if not i_ok:
        return {"authority_resolution_status": "no_identity"}
    if not ac_valid:
        return {"authority_resolution_status": "invalid_claim"}
    return {
        "authority_resolution_status": "resolved",
        "authority_operator_id": identity.get("validated_operator_id"),
        "authority_level": authority_claim.get("authority_level"),
    }
