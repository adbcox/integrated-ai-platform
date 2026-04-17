from dataclasses import dataclass, field

@dataclass
class FileTarget:
    target_id: str
    request_id: str = ""
    file_paths: list[str] = field(default_factory=list)
    target_type: str = ""
    status: str = "planned"
