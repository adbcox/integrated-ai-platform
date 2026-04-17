from dataclasses import dataclass, field

@dataclass
class RunLedger:
    ledger_id: str
    request_ids: list[str] = field(default_factory=list)
    completed_ids: list[str] = field(default_factory=list)
    failed_ids: list[str] = field(default_factory=list)
    status: str = "active"
