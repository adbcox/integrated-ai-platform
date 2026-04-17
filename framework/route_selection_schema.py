from dataclasses import dataclass

@dataclass
class RouteSelection:
    selection_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    selection_reason: str = ""
    status: str = "planned"
