from typing import Any

def execute_intervention(plan: dict, fed_policy_publication: dict, executor_config: dict) -> dict:
    if not isinstance(plan, dict) or not isinstance(fed_policy_publication, dict) or not isinstance(executor_config, dict):
        return {"intervention_execution_status": "invalid_input"}
    p_ok = plan.get("intervention_plan_status") == "planned"
    pub_ok = fed_policy_publication.get("fed_policy_publication_status") == "published"
    if not p_ok:
        return {"intervention_execution_status": "no_plan"}
    if not pub_ok:
        return {"intervention_execution_status": "no_policy"}
    return {
        "intervention_execution_status": "executed",
        "executed_intervention_kind": plan.get("intervention_kind"),
        "executed_directive_id": plan.get("intervention_directive_id"),
        "executed_policy_id": fed_policy_publication.get("published_fed_policy_id"),
    }
