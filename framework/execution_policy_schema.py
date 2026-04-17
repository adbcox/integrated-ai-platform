from dataclasses import dataclass, field

@dataclass
class ExecutionPolicy:
    policy_id: str
    allowed_routes: list[str] = field(default_factory=list)
    default_route: str = "ollama_local"
    allow_fallback: bool = False
    status: str = "active"
