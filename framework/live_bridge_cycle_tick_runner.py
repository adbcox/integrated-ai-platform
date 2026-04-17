from typing import Any

def run_tick(tick_schedule: dict[str, Any], workload_gate: dict[str, Any], runner_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tick_schedule, dict) or not isinstance(workload_gate, dict) or not isinstance(runner_config, dict):
        return {"tick_run_status": "invalid_input", "ran_tick_id": None, "ran_env_id": None}
    ts_ok = tick_schedule.get("tick_schedule_status") == "scheduled"
    wg_open = workload_gate.get("workload_gate_status") == "open"
    if not ts_ok:
        return {"tick_run_status": "not_scheduled", "ran_tick_id": None, "ran_env_id": None}
    if ts_ok and not wg_open:
        return {"tick_run_status": "gate_closed", "ran_tick_id": None, "ran_env_id": None}
    return {"tick_run_status": "ran", "ran_tick_id": tick_schedule.get("tick_id"), "ran_env_id": tick_schedule.get("tick_env_id")} if ts_ok and wg_open else {"tick_run_status": "invalid_input", "ran_tick_id": None, "ran_env_id": None}
