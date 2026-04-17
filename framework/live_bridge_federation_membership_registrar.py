from typing import Any

def register_federation_membership(handshake: dict[str, Any], cycle_completion: dict[str, Any], registrar_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(handshake, dict) or not isinstance(cycle_completion, dict) or not isinstance(registrar_config, dict):
        return {"membership_status": "invalid_input", "member_id": None, "federation_id": None}
    h_ok = handshake.get("handshake_completion_status") == "complete"
    c_ok = cycle_completion.get("cycle_completion_report_status") == "complete"
    if not c_ok:
        return {"membership_status": "cycle_not_complete", "member_id": None, "federation_id": None}
    return {"membership_status": "registered", "member_id": registrar_config.get("member_id", "mem-0001"), "federation_id": registrar_config.get("federation_id", "fed-0001")} if h_ok and c_ok else {"membership_status": "handshake_incomplete", "member_id": None, "federation_id": None}

