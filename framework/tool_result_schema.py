from dataclasses import dataclass, field

@dataclass
class ToolResult:
    tool_name: str
    success: bool = False
    files_touched: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
