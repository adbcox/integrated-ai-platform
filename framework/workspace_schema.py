from dataclasses import dataclass, field

@dataclass
class WorkspaceSchema:
    workspace_id: str
    repo_root: str = ""
    scratch_dir: str = ""
    artifact_dir: str = ""
    allowed_write_paths: list[str] = field(default_factory=list)
    status: str = "planned"
