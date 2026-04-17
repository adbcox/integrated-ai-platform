from typing import Any

def align_federation_clock(tick_run: dict[str, Any], peer_clock: dict[str, Any], aligner_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(tick_run, dict) or not isinstance(peer_clock, dict) or not isinstance(aligner_config, dict):
        return {"clock_alignment_status": "invalid_input", "alignment_drift": None}
    t_ok = tick_run.get("tick_run_status") == "ran"
    drift = abs(peer_clock.get("peer_clock_ts", 0) - aligner_config.get("local_ts", 0))
    max_drift = aligner_config.get("max_drift", 1000)
    if drift > max_drift:
        return {"clock_alignment_status": "drift_exceeded", "alignment_drift": drift}
    return {"clock_alignment_status": "aligned", "alignment_drift": drift} if t_ok else {"clock_alignment_status": "tick_not_ran", "alignment_drift": drift}

