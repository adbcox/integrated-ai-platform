"""Bounded dispatch for PublishArtifactAction -> PublishArtifactObservation via shutil.copy2."""
from __future__ import annotations

import shutil

from framework.tool_schema import PublishArtifactAction, PublishArtifactObservation
from framework.workspace_scope import ToolPathScope


def dispatch_publish_artifact(
    action: PublishArtifactAction,
    scope: ToolPathScope,
) -> PublishArtifactObservation:
    if not isinstance(action, PublishArtifactAction):
        raise TypeError(f"Expected PublishArtifactAction; got {type(action)!r}")
    try:
        source = scope.resolve_path(action.artifact_path, writable=False)
    except PermissionError as exc:
        return PublishArtifactObservation(
            artifact_path=action.artifact_path,
            destination=action.destination,
            published=False,
            error=str(exc),
        )
    try:
        dest = scope.resolve_path(action.destination, writable=True)
    except PermissionError as exc:
        return PublishArtifactObservation(
            artifact_path=action.artifact_path,
            destination=action.destination,
            published=False,
            error=str(exc),
        )
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    except FileNotFoundError as exc:
        return PublishArtifactObservation(
            artifact_path=action.artifact_path,
            destination=action.destination,
            published=False,
            error=str(exc),
        )
    except (PermissionError, OSError) as exc:
        return PublishArtifactObservation(
            artifact_path=action.artifact_path,
            destination=action.destination,
            published=False,
            error=str(exc),
        )
    return PublishArtifactObservation(
        artifact_path=action.artifact_path,
        destination=action.destination,
        published=True,
        error=None,
    )


__all__ = ["dispatch_publish_artifact"]
