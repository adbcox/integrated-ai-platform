from dataclasses import dataclass

@dataclass
class PromptSegment:
    segment_id: str
    request_id: str = ""
    segment_type: str = ""
    content: str = ""
    status: str = "planned"
