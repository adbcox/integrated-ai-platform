from typing import Any

def rollup_cycle(tick_run: dict[str, Any], throughput: dict[str, Any], cycle_reporter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tick_run, dict) or not isinstance(throughput, dict) or not isinstance(cycle_reporter, dict):
        return {"cycle_rollup_status": "invalid_input", "rollup_tick_id": None, "operations_complete": 0}
    all_complete = (tick_run.get("tick_run_status") == "ran" and throughput.get("throughput_status") == "measured" and cycle_reporter.get("cycle_report_status") == "complete")
    if all_complete:
        return {"cycle_rollup_status": "rolled_up", "rollup_tick_id": tick_run.get("ran_tick_id"), "operations_complete": 3}
    return {"cycle_rollup_status": "incomplete_source", "rollup_tick_id": None, "operations_complete": 0}
