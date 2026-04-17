from typing import Any
def negotiate_external_scope(identity: dict[str, Any], scope_resolution: dict[str, Any], negotiator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(identity, dict) or not isinstance(scope_resolution, dict) or not isinstance(negotiator_config, dict):
        return {"scope_negotiation_status": "invalid_input", "negotiated_identity_id": None, "negotiated_scope": None}
    id_ok = identity.get("external_identity_status") == "resolved"
    sr_ok = scope_resolution.get("scope_resolution_status") == "resolved"
    if id_ok and sr_ok:
        return {"scope_negotiation_status": "negotiated", "negotiated_identity_id": identity.get("external_identity_id"), "negotiated_scope": negotiator_config.get("scope", "minimum")}
    return {"scope_negotiation_status": "no_identity" if not id_ok else "no_scope", "negotiated_identity_id": None, "negotiated_scope": None}
