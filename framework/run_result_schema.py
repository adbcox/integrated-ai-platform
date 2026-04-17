from dataclasses import dataclass, field

@dataclass
class RunResult:
    request_id: str
    success: bool = False
    output_files: list[str] = field(default_factory=list)
    validation_summary: str = ""
    error_summary: str = ""
    status: str = "complete"
