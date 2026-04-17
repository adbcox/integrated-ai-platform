from typing import Any
def attach_operator(bridge_cp: dict[str, Any], checklist: dict[str, Any], attachment_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_cp, dict) or not isinstance(checklist, dict) or not isinstance(attachment_config, dict):
        return {"operator_attachment_status": "invalid_input", "attached_env_id": None, "operator_id": None}
    cp_ok = bridge_cp.get("bridge_cp_status") == "operational"
    ch_ok = checklist.get("checklist_status") == "built"
    if cp_ok and ch_ok:
        return {"operator_attachment_status": "attached", "attached_env_id": bridge_cp.get("bridge_cp_env_id"), "operator_id": attachment_config.get("operator_id", "op-0001")}
    return {"operator_attachment_status": "bridge_offline" if not cp_ok else "no_checklist", "attached_env_id": None, "operator_id": None}
