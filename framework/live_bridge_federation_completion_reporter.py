from typing import Any

def report_federation_completion(fed_finalization: dict[str, Any], fed_summary: dict[str, Any], phase_id: str) -> dict[str, Any]:
    if not isinstance(fed_finalization, dict) or not isinstance(fed_summary, dict) or not isinstance(phase_id, str):
        return {"fed_completion_report_status": "invalid_input"}
    f_ok = fed_finalization.get("fed_finalization_status") == "finalized"
    s_ok = fed_summary.get("fed_summary_status") == "complete"
    if not f_ok:
        return {"fed_completion_report_status": "finalization_failed"}
    return {"fed_completion_report_status": "complete"} if f_ok and s_ok else {"fed_completion_report_status": "summary_incomplete"}

