from typing import Any


def rollup_reconciliation(
    exec_result: dict[str, Any],
    audit: dict[str, Any],
    reporter: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(exec_result, dict)
        or not isinstance(audit, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        exec_result.get("execution_status") == "executed"
        and audit.get("audit_status") == "passed"
        and reporter.get("report_status") == "complete"
    )

    if not all_complete:
        count = sum(
            1
            for s in [
                exec_result.get("execution_status"),
                audit.get("audit_status"),
                reporter.get("report_status"),
            ]
            if s in ("executed", "passed", "complete")
        )
        return {
            "rollup_status": "incomplete_source",
            "rollup_phase": None,
            "operations_complete": count,
        }

    return {
        "rollup_status": "rolled_up",
        "rollup_phase": exec_result.get("executed_phase"),
        "operations_complete": 3,
    }
