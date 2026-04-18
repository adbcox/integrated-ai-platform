from typing import Any

def build_postmortem(incident_closure: Any, postmortem_config: Any) -> dict[str, Any]:
    if not isinstance(incident_closure, dict):
        return {"postmortem_building_status": "not_built"}
    close_ok = incident_closure.get("incident_closure_status") == "closed"
    if not close_ok:
        return {"postmortem_building_status": "not_built"}
    return {
        "postmortem_building_status": "built",
        "postmortem_id": postmortem_config.get("postmortem_id", "PM_0"),
    }
