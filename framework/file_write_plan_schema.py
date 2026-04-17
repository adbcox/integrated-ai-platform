from dataclasses import dataclass, field

@dataclass
class FileWritePlan:
    plan_id: str
    request_id: str = ""
    target_paths: list[str] = field(default_factory=list)
    write_mode: str = ""
    status: str = "planned"
