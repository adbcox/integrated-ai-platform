from typing import Any

def route_affinity(admission: dict[str, Any], broker: dict[str, Any], affinity_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(admission, dict) or not isinstance(broker, dict) or not isinstance(affinity_config, dict):
        return {"affinity_routing_status": "invalid_input", "routed_session_id": None}
    a_ok = admission.get("admission_status") == "admitted"
    b_ok = broker.get("session_broker_status") == "brokered"
    return {"affinity_routing_status": "routed", "routed_session_id": broker.get("brokered_session_id")} if a_ok and b_ok else {"affinity_routing_status": "prerequisites_failed", "routed_session_id": None}

