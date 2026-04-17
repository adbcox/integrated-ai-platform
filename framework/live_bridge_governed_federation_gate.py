from typing import Any

def gate_governed_federation(fed_gov_summary: dict, fed_seal: dict, fed_completion: dict) -> dict:
    if not isinstance(fed_gov_summary, dict) or not isinstance(fed_seal, dict) or not isinstance(fed_completion, dict):
        return {"governed_fed_gate_status": "invalid_input"}
    fs_ok = fed_gov_summary.get("fed_gov_summary_status") == "complete"
    seal_ok = fed_seal.get("fed_seal_status") == "sealed"
    fc_ok = fed_completion.get("fed_completion_report_status") == "complete"
    all_ok = fs_ok and seal_ok and fc_ok
    any_ok = fs_ok or seal_ok or fc_ok
    if all_ok:
        return {
            "governed_fed_gate_status": "open",
            "gate_env_id": fed_gov_summary.get("summary_fed_gov_env_id"),
            "gate_signals": 3,
        }
    if any_ok:
        return {"governed_fed_gate_status": "partial", "gate_signals": int(fs_ok) + int(seal_ok) + int(fc_ok)}
    return {"governed_fed_gate_status": "closed", "gate_signals": 0}
