from typing import Any

def register_operator(fed_seal: dict, operator_descriptor: dict, registrar_config: dict) -> dict:
    if not isinstance(fed_seal, dict) or not isinstance(operator_descriptor, dict) or not isinstance(registrar_config, dict):
        return {"operator_registration_status": "invalid_input"}
    s_ok = fed_seal.get("fed_seal_status") == "sealed"
    od_valid = bool(operator_descriptor.get("operator_id")) and bool(operator_descriptor.get("operator_kind"))
    if not s_ok:
        return {"operator_registration_status": "not_sealed"}
    if not od_valid:
        return {"operator_registration_status": "invalid_descriptor"}
    return {
        "operator_registration_status": "registered",
        "operator_id": operator_descriptor.get("operator_id"),
        "operator_kind": operator_descriptor.get("operator_kind"),
        "operator_env_id": fed_seal.get("sealed_fed_env_id"),
    }
