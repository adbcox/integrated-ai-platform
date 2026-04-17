from typing import Any

def route_escalation(directive_dispatch: dict, quorum_validation: dict, router_config: dict) -> dict:
    if not isinstance(directive_dispatch, dict) or not isinstance(quorum_validation, dict) or not isinstance(router_config, dict):
        return {"escalation_status": "invalid_input"}
    dd_ok = directive_dispatch.get("directive_dispatch_status") == "dispatched"
    qv_ok = quorum_validation.get("quorum_validation_status") == "valid"
    if not dd_ok:
        return {"escalation_status": "no_dispatch"}
    if not qv_ok:
        return {"escalation_status": "no_quorum"}
    return {
        "escalation_status": "routed",
        "escalated_directive_id": directive_dispatch.get("dispatched_directive_id"),
        "escalation_tier": router_config.get("tier", "tier-1"),
    }
