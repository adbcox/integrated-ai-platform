from typing import Any


def rollup_knowledge(
    synthesis: dict[str, Any], strategy: dict[str, Any], reporter: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(synthesis, dict)
        or not isinstance(strategy, dict)
        or not isinstance(reporter, dict)
    ):
        return {
            "knowledge_rollup_status": "invalid_input",
            "rollup_phase": None,
            "operations_complete": 0,
        }

    all_complete = (
        synthesis.get("synthesis_status") == "synthesized"
        and strategy.get("strategy_status") == "learned"
        and reporter.get("learning_report_status") == "complete"
    )
    count = sum(
        1
        for s, vals in [
            (synthesis.get("synthesis_status"), ("synthesized",)),
            (strategy.get("strategy_status"), ("learned",)),
            (reporter.get("learning_report_status"), ("complete",)),
        ]
        if s in vals
    )

    if all_complete:
        return {
            "knowledge_rollup_status": "rolled_up",
            "rollup_phase": reporter.get("report_phase"),
            "operations_complete": count,
        }

    return {
        "knowledge_rollup_status": "incomplete_source",
        "rollup_phase": None,
        "operations_complete": count,
    }
