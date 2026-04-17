from typing import Any
def resolve_external_identity(session_validation: dict[str, Any], identity_claim: dict[str, Any], resolver_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(session_validation, dict) or not isinstance(identity_claim, dict) or not isinstance(resolver_config, dict):
        return {"external_identity_status": "invalid_input", "external_identity_id": None, "resolver_session_id": None}
    sv_ok = session_validation.get("session_validation_status") == "valid"
    id_ok = bool(identity_claim.get("identity_id"))
    if sv_ok and id_ok:
        return {"external_identity_status": "resolved", "external_identity_id": identity_claim.get("identity_id"), "resolver_session_id": session_validation.get("validated_session_id")}
    return {"external_identity_status": "no_session" if not sv_ok else "no_claim", "external_identity_id": None, "resolver_session_id": None}
