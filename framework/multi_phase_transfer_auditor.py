from typing import Any


def audit_transfer(
    transfer_execution: dict[str, Any],
    mastery_assessment: dict[str, Any],
    audit_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_execution, dict)
        or not isinstance(mastery_assessment, dict)
        or not isinstance(audit_config, dict)
    ):
        return {
            "transfer_audit_status": "invalid_input",
            "audited_phase": None,
            "audit_result": None,
        }

    te_ok = transfer_execution.get("transfer_execution_status") == "executed"
    ma_ok = mastery_assessment.get("mastery_status") == "assessed"
    all_ok = te_ok and ma_ok

    if all_ok:
        return {
            "transfer_audit_status": "passed",
            "audited_phase": transfer_execution.get("executed_phase"),
            "audit_result": "transfer_and_mastery_complete",
        }

    if te_ok or ma_ok:
        return {
            "transfer_audit_status": "degraded",
            "audited_phase": None,
            "audit_result": "partial_completion",
        }

    return {
        "transfer_audit_status": "failed",
        "audited_phase": None,
        "audit_result": "no_transfer_or_mastery",
    }
