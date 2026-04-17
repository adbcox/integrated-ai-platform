from typing import Any


def rollup_decisions(
    arbitration: dict[str, Any],
    recording: dict[str, Any],
    reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(arbitration, dict)
        or not isinstance(recording, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "decision_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        arbitration.get("arbitration_status") == "arbitrated"
        and recording.get("recording_status") == "recorded"
        and reporter.get("autonomy_report_status") == "complete"
    )

    count = sum(
        1
        for s, vals in [
            (arbitration.get("arbitration_status"), ("arbitrated",)),
            (recording.get("recording_status"), ("recorded",)),
            (reporter.get("autonomy_report_status"), ("complete",)),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "decision_rollup_status": "rolled_up",
            "rollup_phase": reporter.get("report_phase"),
            "operations_complete": count,
        }

    return {
        "decision_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
