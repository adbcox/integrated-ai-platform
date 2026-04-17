from typing import Any

def seal_federation_handshake(fed_completion: dict[str, Any], peer_rollup: dict[str, Any], sealer_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_completion, dict) or not isinstance(peer_rollup, dict) or not isinstance(sealer_config, dict):
        return {"fed_seal_status": "invalid_input"}
    c_ok = fed_completion.get("fed_completion_report_status") == "complete"
    p_ok = peer_rollup.get("fed_peer_rollup_status") == "rolled_up"
    if not c_ok:
        return {"fed_seal_status": "completion_not_complete"}
    return {"fed_seal_status": "sealed"} if c_ok and p_ok else {"fed_seal_status": "peer_rollup_incomplete"}

