from dataclasses import dataclass, field

@dataclass
class RouteSummary:
    summary_id: str
    request_ids: list[str] = field(default_factory=list)
    selected_routes: list[str] = field(default_factory=list)
    summary_state: str = "complete"
    notes: str = ""
