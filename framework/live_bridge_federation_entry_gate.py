from typing import Any

def gate_federation_entry(fed_summary: dict[str, Any], fed_health: dict[str, Any], cycle_completion: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_summary, dict) or not isinstance(fed_health, dict) or not isinstance(cycle_completion, dict):
        return {"fed_entry_gate_status": "invalid_input"}
    s_ok = fed_summary.get("fed_summary_status") == "complete"
    h_ok = fed_health.get("fed_health_status") == "green"
    c_ok = cycle_completion.get("cycle_completion_report_status") == "complete"
    all_ok = s_ok and h_ok and c_ok
    return {"fed_entry_gate_status": "open"} if all_ok else {"fed_entry_gate_status": "closed"}

