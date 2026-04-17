from dataclasses import dataclass, field

@dataclass
class SessionPromptPlan:
    plan_id: str
    session_id: str = ""
    prompt_ids: list[str] = field(default_factory=list)
    selected_route: str = "ollama_local"
    status: str = "planned"
