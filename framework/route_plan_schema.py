from dataclasses import dataclass, field

@dataclass
class RoutePlan:
    plan_id: str
    request_id: str = ""
    candidate_routes: list[str] = field(default_factory=list)
    preferred_route: str = "ollama_local"
    status: str = "planned"
