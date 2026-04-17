from dataclasses import dataclass

@dataclass
class RouteAudit:
    audit_id: str
    request_id: str = ""
    selected_route: str = "ollama_local"
    audit_reason: str = ""
    status: str = "complete"
