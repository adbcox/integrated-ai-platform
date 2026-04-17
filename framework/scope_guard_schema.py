from dataclasses import dataclass, field

@dataclass
class ScopeGuard:
    allowed_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    stop_on_scope_violation: bool = True
    scope_status: str = "planned"
    details: str = ""
