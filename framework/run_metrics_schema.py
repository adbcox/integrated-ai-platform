from dataclasses import dataclass, field

@dataclass
class RunMetrics:
    metrics_id: str
    request_id: str = ""
    counters: list[str] = field(default_factory=list)
    measurements: list[str] = field(default_factory=list)
    status: str = "complete"
