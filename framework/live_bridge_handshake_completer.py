from typing import Any
def complete_handshake(operator_attachment: dict[str, Any], phase6_entry_report: dict[str, Any], external_manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(operator_attachment, dict) or not isinstance(phase6_entry_report, dict) or not isinstance(external_manifest, dict):
        return {"handshake_status": "invalid_input", "handshake_env_id": None, "handshake_signals": 0}
    oa_ok = operator_attachment.get("operator_attachment_status") == "attached"
    per_ok = phase6_entry_report.get("phase6_entry_report_status") == "complete"
    em_ok = external_manifest.get("external_manifest_status") == "built"
    all_ok = oa_ok and per_ok and em_ok
    any_ok = oa_ok or per_ok or em_ok
    if all_ok:
        return {"handshake_status": "completed", "handshake_env_id": operator_attachment.get("attached_env_id"), "handshake_signals": 3}
    if any_ok:
        return {"handshake_status": "partial", "handshake_env_id": None, "handshake_signals": sum([oa_ok, per_ok, em_ok])}
    return {"handshake_status": "failed", "handshake_env_id": None, "handshake_signals": 0}
