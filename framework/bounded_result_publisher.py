"""BoundedResultPublisher: copies a loop result artifact to a stable publication destination."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.publish_artifact_dispatch import dispatch_publish_artifact
from framework.tool_schema import PublishArtifactAction, PublishArtifactObservation
from framework.workspace_scope import ToolPathScope

# -- import-time assertions --
assert "published" in PublishArtifactObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: PublishArtifactObservation.published"
assert "artifact_path" in PublishArtifactObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: PublishArtifactObservation.artifact_path"
assert "error" in PublishArtifactObservation.__dataclass_fields__, \
    "INTERFACE MISMATCH: PublishArtifactObservation.error"
assert callable(dispatch_publish_artifact), \
    "INTERFACE MISMATCH: dispatch_publish_artifact"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class PublicationRecord:
    session_id: str
    artifact_path: str
    destination: str
    published: bool
    publication_error: Optional[str]
    published_at: str


class BoundedResultPublisher:
    """Copies a loop result artifact via dispatch_publish_artifact; failure non-raising."""

    def __init__(self, *, artifact_dir: Optional[Path] = None):
        self._artifact_dir = Path(artifact_dir) if artifact_dir is not None else Path("artifacts")

    def publish(
        self,
        session_id: str,
        artifact_path: str,
        *,
        scope: Optional[ToolPathScope] = None,
    ) -> PublicationRecord:
        dest_dir = self._artifact_dir / session_id
        destination = str(dest_dir / Path(artifact_path).name)

        published = False
        publication_error: Optional[str] = None

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if scope is None:
                # Use the artifact file path itself as source_root so dest_dir
                # is never considered "inside" source_root (a file path can't
                # be a parent of the destination directory).
                artifact_abs = Path(artifact_path).resolve()
                scope = ToolPathScope(source_root=artifact_abs, writable_roots=(str(dest_dir),))
            action = PublishArtifactAction(artifact_path=artifact_path, destination=destination)
            obs: PublishArtifactObservation = dispatch_publish_artifact(action, scope)
            published = bool(obs.published)
            publication_error = obs.error
        except Exception as exc:
            publication_error = str(exc)

        return PublicationRecord(
            session_id=session_id,
            artifact_path=artifact_path,
            destination=destination,
            published=published,
            publication_error=publication_error,
            published_at=_iso_now(),
        )


__all__ = ["PublicationRecord", "BoundedResultPublisher"]
