from dataclasses import dataclass, field

@dataclass
class ScopeResult:
    result_id: str
    allowed_files: list[str] = field(default_factory=list)
    touched_files: list[str] = field(default_factory=list)
    scope_passed: bool = False
    details: str = ""
