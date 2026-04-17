from dataclasses import dataclass

@dataclass
class WriteIntent:
    intent_id: str
    request_id: str = ""
    target_path: str = ""
    intent_type: str = ""
    status: str = "planned"
