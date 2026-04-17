from dataclasses import dataclass

@dataclass
class SessionRouteRecord:
    record_id: str
    session_id: str = ""
    selected_route: str = "ollama_local"
    route_reason: str = ""
    status: str = "complete"
