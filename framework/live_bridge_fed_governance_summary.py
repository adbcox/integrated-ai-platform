from typing import Any

def summarize_fed_governance(fed_gov_cp: dict, operator_rollup: dict, supervisory_rollup: dict) -> dict:
    if not isinstance(fed_gov_cp, dict) or not isinstance(operator_rollup, dict) or not isinstance(supervisory_rollup, dict):
        return {"fed_gov_summary_status": "invalid_input"}
    cp_op = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    or_ok = operator_rollup.get("operator_rollup_status") == "rolled_up"
    sr_ok = supervisory_rollup.get("supervisory_rollup_status") == "rolled_up"
    if cp_op and or_ok and sr_ok:
        return {
            "fed_gov_summary_status": "complete",
            "summary_fed_gov_env_id": fed_gov_cp.get("fed_gov_cp_env_id"),
            "fed_gov_health": "governed",
        }
    if cp_op and (not or_ok or not sr_ok):
        return {"fed_gov_summary_status": "partial", "fed_gov_health": "pending"}
    return {"fed_gov_summary_status": "failed", "fed_gov_health": "pending"}
