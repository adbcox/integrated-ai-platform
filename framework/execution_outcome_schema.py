from dataclasses import dataclass

@dataclass
class ExecutionOutcome:
    outcome_class: str
    error_category: str = ""
    recovery_attempted: bool = False
    validation_passed: bool = False
    notes: str = ""
