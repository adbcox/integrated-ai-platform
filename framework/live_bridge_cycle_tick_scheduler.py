from typing import Any

def schedule_tick(bridge_cp: dict[str, Any], tick_config: dict[str, Any], tick_counter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_cp, dict) or not isinstance(tick_config, dict) or not isinstance(tick_counter, dict):
        return {"tick_schedule_status": "invalid_input", "tick_id": 0, "tick_at": None, "tick_env_id": None}
    cp_op = bridge_cp.get("bridge_cp_status") == "operational"
    if not cp_op:
        return {"tick_schedule_status": "bridge_offline", "tick_id": 0, "tick_at": None, "tick_env_id": None}
    return {"tick_schedule_status": "scheduled", "tick_id": int(tick_counter.get("count", 0)) + 1, "tick_at": tick_config.get("timestamp", "t-0001"), "tick_env_id": bridge_cp.get("bridge_cp_env_id")} if cp_op else {"tick_schedule_status": "invalid_input", "tick_id": 0, "tick_at": None, "tick_env_id": None}
