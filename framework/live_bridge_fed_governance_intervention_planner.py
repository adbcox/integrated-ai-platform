from typing import Any

def plan_intervention(override: dict, veto: dict, rollback: dict) -> dict:
    if not isinstance(override, dict) or not isinstance(veto, dict) or not isinstance(rollback, dict):
        return {"intervention_plan_status": "invalid_input"}
    o_applied = override.get("override_status") == "applied"
    v_applied = veto.get("veto_status") == "applied"
    r_applied = rollback.get("rollback_status") == "applied"
    any_applied = o_applied or v_applied or r_applied
    if not any_applied:
        return {"intervention_plan_status": "no_action"}
    if o_applied:
        kind = "override"
        did = override.get("override_directive_id")
    elif v_applied:
        kind = "veto"
        did = veto.get("veto_directive_id")
    else:
        kind = "rollback"
        did = rollback.get("rollback_directive_id")
    return {
        "intervention_plan_status": "planned",
        "intervention_kind": kind,
        "intervention_directive_id": did,
    }
