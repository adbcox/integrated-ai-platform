from typing import Any


def rollup_transfer(
    transfer_executor: dict[str, Any],
    transfer_auditor: dict[str, Any],
    cross_phase_applier: dict[str, Any],
    rollup_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_executor, dict)
        or not isinstance(transfer_auditor, dict)
        or not isinstance(cross_phase_applier, dict)
        or not isinstance(rollup_config, dict)
    ):
        return {
            "transfer_rollup_status": "invalid_input",
            "rollup_phase": None,
            "transfer_scope": None,
        }

    te_ok = transfer_executor.get("transfer_execution_status") == "executed"
    ta_ok = transfer_auditor.get("transfer_audit_status") == "passed"
    cpa_ok = cross_phase_applier.get("application_status") == "applied"
    all_ok = te_ok and ta_ok and cpa_ok

    if all_ok:
        return {
            "transfer_rollup_status": "rolled_up",
            "rollup_phase": transfer_executor.get("executed_phase"),
            "transfer_scope": rollup_config.get("scope", "cross_phase"),
        }

    if (te_ok and ta_ok) or (te_ok and cpa_ok) or (ta_ok and cpa_ok):
        return {
            "transfer_rollup_status": "degraded",
            "rollup_phase": None,
            "transfer_scope": None,
        }

    return {
        "transfer_rollup_status": "offline",
        "rollup_phase": None,
        "transfer_scope": None,
    }
