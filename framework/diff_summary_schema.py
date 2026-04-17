from dataclasses import dataclass, field

@dataclass
class DiffSummary:
    diff_id: str
    request_id: str = ""
    files_added: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    status: str = "complete"
