from dataclasses import dataclass, field

@dataclass
class PromptEnvelope:
    envelope_id: str
    request_id: str = ""
    segments: list[str] = field(default_factory=list)
    target_route: str = "ollama_local"
    status: str = "planned"
