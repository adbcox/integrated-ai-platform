from typing import Any

def control_veto(dispatch: dict, normalization: dict, veto_config: dict) -> dict:
    if not isinstance(dispatch, dict) or not isinstance(normalization, dict) or not isinstance(veto_config, dict):
        return {"veto_status": "invalid_input"}
    d_ok = dispatch.get("directive_dispatch_status") == "dispatched"
    is_veto = normalization.get("normalized_kind") == "veto"
    if not d_ok:
        return {"veto_status": "no_dispatch"}
    if not is_veto:
        return {"veto_status": "not_veto"}
    return {
        "veto_status": "applied",
        "veto_directive_id": dispatch.get("dispatched_directive_id"),
        "veto_scope": veto_config.get("scope", "federation"),
    }
