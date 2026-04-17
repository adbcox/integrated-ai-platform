from dataclasses import dataclass, field

@dataclass
class FileWriteResult:
    result_id: str
    request_id: str = ""
    written_paths: list[str] = field(default_factory=list)
    write_state: str = "complete"
    notes: str = ""
