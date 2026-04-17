from typing import Any
def publish_response(composition: dict[str, Any], egress: dict[str, Any], publisher_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(composition, dict) or not isinstance(egress, dict) or not isinstance(publisher_config, dict):
        return {"response_publication_status": "invalid_input", "published_response_id": None, "published_channel_id": None}
    c_ok = composition.get("response_composition_status") == "composed"
    e_ok = egress.get("egress_channel_status") == "built"
    if c_ok and e_ok:
        return {"response_publication_status": "published", "published_response_id": composition.get("response_id"), "published_channel_id": egress.get("egress_channel_id")}
    return {"response_publication_status": "not_composed" if not c_ok else "no_egress", "published_response_id": None, "published_channel_id": None}
