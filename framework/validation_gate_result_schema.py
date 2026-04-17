from dataclasses import dataclass

@dataclass
class ValidationGateResult:
    gate_result_id: str
    gate_name: str = ""
    passed: bool = False
    details: str = ""
    status: str = "complete"
