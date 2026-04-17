from typing import Any

def rollup_fed_governance(fed_policy_publication: dict, intervention_execution: dict, fed_gov_report: dict) -> dict:
    if not isinstance(fed_policy_publication, dict) or not isinstance(intervention_execution, dict) or not isinstance(fed_gov_report, dict):
        return {"fed_gov_rollup_status": "invalid_input"}
    all_complete = (
        fed_policy_publication.get("fed_policy_publication_status") == "published" and
        intervention_execution.get("intervention_execution_status") == "executed" and
        fed_gov_report.get("fed_gov_report_status") == "complete"
    )
    if all_complete:
        return {
            "fed_gov_rollup_status": "rolled_up",
            "rollup_policy_id": fed_policy_publication.get("published_fed_policy_id"),
            "operations_complete": 3,
        }
    return {"fed_gov_rollup_status": "incomplete_source", "operations_complete": 0}
