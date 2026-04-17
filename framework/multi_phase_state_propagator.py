from typing import Any

def propagate_phase_state(seed: dict, terminal_report: dict, target_phase: str) -> dict:
    if not isinstance(seed, dict) or not isinstance(terminal_report, dict):
        return {"propagation_status": "invalid_input"}
    
    seed_ready = seed.get("seed_ready", False)
    terminal_status = terminal_report.get("terminal_status")
    
    if not seed_ready or terminal_status != "complete":
        return {"propagation_status": "source_incomplete"}
    
    if not isinstance(target_phase, str) or not target_phase:
        return {"propagation_status": "invalid_input"}
    
    approved_releases = seed.get("seed_payload", {}).get("approved_releases", 0)
    terminal_status = seed.get("seed_payload", {}).get("terminal_status", "")
    
    return {
        "propagation_status": "propagated",
        "propagated_phase": target_phase,
        "state_snapshot": {
            "approved_releases": approved_releases,
            "terminal_status": terminal_status
        }
    }
