from dataclasses import dataclass, field

@dataclass
class ScopeAuditResult:
    audit_result_id: str
    request_id: str = ""
    allowed_files: list[str] = field(default_factory=list)
    out_of_scope_files: list[str] = field(default_factory=list)
    status: str = "complete"
