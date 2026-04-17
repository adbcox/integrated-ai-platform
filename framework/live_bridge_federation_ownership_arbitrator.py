from typing import Any

def arbitrate_ownership(resolution: dict[str, Any], broker: dict[str, Any], arbitrator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(resolution, dict) or not isinstance(broker, dict) or not isinstance(arbitrator_config, dict):
        return {"ownership_status": "invalid_input", "owner_id": None}
    r_ok = resolution.get("resolution_status") in ("resolved", "no_conflict")
    b_ok = broker.get("session_broker_status") == "brokered"
    return {"ownership_status": "arbitrated", "owner_id": arbitrator_config.get("owner_id", "own-0001")} if r_ok and b_ok else {"ownership_status": "prerequisites_failed", "owner_id": None}

