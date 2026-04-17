from typing import Any


def plan_reconciliation(
    sync_result: dict[str, Any],
    divergence: dict[str, Any],
    coordinator: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(sync_result, dict)
        or not isinstance(divergence, dict)
        or not isinstance(coordinator, dict)
    ):
        return {
            "reconciliation_status": "invalid_input",
            "reconciliation_phase": None,
            "delta": None,
        }

    needs_reconciliation = (
        sync_result.get("sync_status") == "sync_required"
        or divergence.get("divergence_status") == "diverged"
    )
    all_synced = (
        sync_result.get("sync_status") == "synced"
        and divergence.get("divergence_status") == "no_divergence"
    )

    if all_synced:
        return {
            "reconciliation_status": "already_synced",
            "reconciliation_phase": None,
            "delta": None,
        }

    if (
        needs_reconciliation
        and coordinator.get("coordinator_status") != "initialized"
    ):
        return {
            "reconciliation_status": "coordinator_not_ready",
            "reconciliation_phase": None,
            "delta": None,
        }

    if (
        needs_reconciliation
        and coordinator.get("coordinator_status") == "initialized"
    ):
        return {
            "reconciliation_status": "planned",
            "reconciliation_phase": coordinator.get("phase_id"),
            "delta": divergence.get("delta"),
        }

    return {
        "reconciliation_status": "invalid_input",
        "reconciliation_phase": None,
        "delta": None,
    }
