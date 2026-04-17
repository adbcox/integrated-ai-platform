from dataclasses import dataclass, field

@dataclass
class RouteConstraint:
    constraint_id: str
    allowed_routes: list[str] = field(default_factory=list)
    preferred_route: str = "ollama_local"
    fallback_allowed: bool = False
    status: str = "active"
