from dataclasses import dataclass, field

@dataclass
class ValidationGate:
    gate_name: str
    passed: bool = False
    details: str = ""
    blocking: bool = True
    files_checked: list[str] = field(default_factory=list)
