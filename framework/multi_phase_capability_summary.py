from typing import Any


def summarize_capability(
    transfer_summary: dict[str, Any],
    generalization_summary: dict[str, Any],
    summary_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_summary, dict)
        or not isinstance(generalization_summary, dict)
        or not isinstance(summary_config, dict)
    ):
        return {
            "capability_summary_status": "invalid_input",
            "summary_phase": None,
            "capability_level": None,
        }

    ts_ok = transfer_summary.get("transfer_summary_status") == "complete"
    gs_ok = generalization_summary.get("generalization_summary_status") == "complete"
    all_ok = ts_ok and gs_ok

    if all_ok:
        return {
            "capability_summary_status": "complete",
            "summary_phase": transfer_summary.get("summary_phase"),
            "capability_level": summary_config.get("level", "advanced"),
        }

    if ts_ok or gs_ok:
        return {
            "capability_summary_status": "partial",
            "summary_phase": None,
            "capability_level": None,
        }

    return {
        "capability_summary_status": "incomplete",
        "summary_phase": None,
        "capability_level": None,
    }
