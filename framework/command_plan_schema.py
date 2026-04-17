from dataclasses import dataclass, field

@dataclass
class CommandPlan:
    plan_id: str
    request_id: str = ""
    commands: list[str] = field(default_factory=list)
    working_directory: str = ""
    status: str = "planned"
