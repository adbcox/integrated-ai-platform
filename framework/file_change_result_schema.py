from dataclasses import dataclass, field

@dataclass
class FileChangeResult:
    result_id: str
    request_id: str = ""
    changed_files: list[str] = field(default_factory=list)
    change_status: str = "complete"
    notes: str = ""
