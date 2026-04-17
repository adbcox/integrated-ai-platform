from typing import Any


def collect_evidence(
    exit_finalization: dict[str, Any],
    capability_summary: dict[str, Any],
    collector_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(exit_finalization, dict)
        or not isinstance(capability_summary, dict)
        or not isinstance(collector_config, dict)
    ):
        return {
            "evidence_status": "invalid_input",
            "evidence_phase": None,
            "evidence_count": 0,
        }

    ef_ok = exit_finalization.get("exit_finalization_status") == "finalized"
    cs_ok = capability_summary.get("capability_summary_status") == "complete"

    if ef_ok and cs_ok:
        return {
            "evidence_status": "collected",
            "evidence_phase": exit_finalization.get("exit_phase"),
            "evidence_count": capability_summary.get("summary_count", 0),
        }

    return {
        "evidence_status": "failed",
        "evidence_phase": None,
        "evidence_count": 0,
    }
