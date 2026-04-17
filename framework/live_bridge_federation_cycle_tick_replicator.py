from typing import Any

def replicate_tick(sync: dict[str, Any], tick_run: dict[str, Any], replicator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(sync, dict) or not isinstance(tick_run, dict) or not isinstance(replicator_config, dict):
        return {"tick_replication_status": "invalid_input", "replicated_peer_count": 0}
    s_ok = sync.get("sync_status") == "synced"
    t_ok = tick_run.get("tick_run_status") == "ran"
    if not s_ok:
        return {"tick_replication_status": "sync_not_synced", "replicated_peer_count": 0}
    peer_count = sync.get("synced_peer_count", 0)
    return {"tick_replication_status": "replicated", "replicated_peer_count": peer_count} if s_ok and t_ok else {"tick_replication_status": "tick_not_ran", "replicated_peer_count": 0}

