from typing import Any

def summarize_obs(obs_cp: Any) -> dict[str, Any]:
    if not isinstance(obs_cp, dict):
        return {"obs_summary_status": "not_summarized"}
    cp_ok = obs_cp.get("obs_cp_status") == "operational"
    if not cp_ok:
        return {"obs_summary_status": "not_summarized"}
    return {
        "obs_summary_status": "summarized",
    }
