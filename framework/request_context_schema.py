from dataclasses import dataclass, field

@dataclass
class RequestContext:
    context_id: str
    request_id: str = ""
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    status: str = "planned"
