from typing import Any
def compose_response(translation: dict[str, Any], routing: dict[str, Any], composer_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(translation, dict) or not isinstance(routing, dict) or not isinstance(composer_config, dict):
        return {"response_composition_status": "invalid_input", "response_operation_id": None, "response_id": None}
    t_ok = translation.get("event_translation_status") == "translated"
    r_ok = routing.get("autonomy_routing_status") == "routed"
    if t_ok and r_ok:
        return {"response_composition_status": "composed", "response_operation_id": routing.get("routed_operation_id"), "response_id": composer_config.get("response_id", "resp-0001")}
    return {"response_composition_status": "not_translated" if not t_ok else "not_routed", "response_operation_id": None, "response_id": None}
