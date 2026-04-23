from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    validation_name: str
    passed: bool = False
    details: str = ""
    files_checked: list[str] = field(default_factory=list)
