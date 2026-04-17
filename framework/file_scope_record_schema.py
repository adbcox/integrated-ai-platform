from dataclasses import dataclass, field

@dataclass
class FileScopeRecord:
    record_id: str
    request_id: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    touched_paths: list[str] = field(default_factory=list)
    status: str = "complete"
