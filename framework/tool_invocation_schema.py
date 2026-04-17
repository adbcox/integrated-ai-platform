from dataclasses import dataclass, field

@dataclass
class ToolInvocation:
    invocation_id: str
    tool_name: str = ""
    request_id: str = ""
    arguments: list[str] = field(default_factory=list)
    status: str = "planned"
