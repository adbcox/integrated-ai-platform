from typing import Any

def gate_governed_federation_stability(governed_fed_gate: dict, fed_gov_cp: dict, supervisory_health: dict) -> dict:
    if not isinstance(governed_fed_gate, dict) or not isinstance(fed_gov_cp, dict) or not isinstance(supervisory_health, dict):
        return {"governed_fed_stability_gate_status": "invalid_input"}
    gg_open = governed_fed_gate.get("governed_fed_gate_status") == "open"
    cp_op = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    sh_green = supervisory_health.get("supervisory_health_status") == "green"
    all_ok = gg_open and cp_op and sh_green
    any_ok = gg_open or cp_op or sh_green
    if all_ok:
        return {
            "governed_fed_stability_gate_status": "stable",
            "stability_env_id": fed_gov_cp.get("fed_gov_cp_env_id"),
            "stability_signals": 3,
        }
    if any_ok:
        return {"governed_fed_stability_gate_status": "degraded", "stability_signals": int(gg_open) + int(cp_op) + int(sh_green)}
    return {"governed_fed_stability_gate_status": "unstable", "stability_signals": 0}
