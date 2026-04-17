from typing import Any

def bridge_checkpoint_to_phase5(completion_ledger: dict, readiness_ledger: dict, seed: dict) -> dict:
    if not isinstance(completion_ledger, dict) or not isinstance(readiness_ledger, dict) or not isinstance(seed, dict):
        return {"bridge_status": "invalid_input"}
    
    all_complete = completion_ledger.get("ledger_status") == "complete" and readiness_ledger.get("ledger_status") == "ready" and seed.get("seed_ready", False)
    
    if not all_complete:
        return {"bridge_status": "incomplete_source"}
    
    phase_id = seed.get("seed_payload", {}).get("target_phase", "phase-5")
    approved_releases = seed.get("seed_payload", {}).get("approved_releases", 0)
    
    return {
        "bridge_status": "bridged",
        "bridged_phase": phase_id,
        "approved_releases": approved_releases
    }
