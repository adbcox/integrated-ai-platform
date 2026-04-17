from dataclasses import dataclass, field

@dataclass
class CommandResult:
    result_id: str
    request_id: str = ""
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    status: str = "complete"
