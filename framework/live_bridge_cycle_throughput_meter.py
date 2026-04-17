from typing import Any

def meter_throughput(tick_run: dict[str, Any], completion: dict[str, Any], meter_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tick_run, dict) or not isinstance(completion, dict) or not isinstance(meter_config, dict):
        return {"throughput_status": "invalid_input", "throughput_tick_id": None, "ops_per_tick": 0}
    tr_ok = tick_run.get("tick_run_status") == "ran"
    c_ok = completion.get("completion_status") == "completed"
    if not tr_ok:
        return {"throughput_status": "no_run", "throughput_tick_id": None, "ops_per_tick": 0}
    if tr_ok and not c_ok:
        return {"throughput_status": "no_completion", "throughput_tick_id": None, "ops_per_tick": 0}
    return {"throughput_status": "measured", "throughput_tick_id": tick_run.get("ran_tick_id"), "ops_per_tick": meter_config.get("ops_per_tick", 1)} if tr_ok and c_ok else {"throughput_status": "invalid_input", "throughput_tick_id": None, "ops_per_tick": 0}
