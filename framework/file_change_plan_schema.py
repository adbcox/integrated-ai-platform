from dataclasses import dataclass, field

@dataclass
class FileChangePlan:
    plan_id: str
    request_id: str = ""
    target_files: list[str] = field(default_factory=list)
    change_kind: str = ""
    status: str = "planned"
