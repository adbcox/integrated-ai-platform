"""Typed Action→Observation contract surface for the 9 minimum runtime tools.

Stdlib-only module. No imports from other framework modules.

Declares the minimum typed contract opener for the shared agent runtime substrate.
Dispatch, permission checks, sandboxing, workspace lifecycle, and wire-format
serialization are out of scope for this seam.

Format contract: governance/tool_contract_spec.json
Schema version:  1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ToolAction:
    """Base marker for all typed tool action requests."""


@dataclass(frozen=True)
class ToolObservation:
    """Base marker for all typed tool observation responses."""


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReadFileAction(ToolAction):
    path: str


@dataclass(frozen=True)
class ReadFileObservation(ToolObservation):
    path: str
    content: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SearchAction(ToolAction):
    query: str
    path: str = "."
    pattern: Optional[str] = None


@dataclass(frozen=True)
class SearchObservation(ToolObservation):
    query: str
    matches: tuple = ()
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# list_dir
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ListDirAction(ToolAction):
    path: str


@dataclass(frozen=True)
class ListDirObservation(ToolObservation):
    path: str
    entries: tuple = ()
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# repo_map
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RepoMapAction(ToolAction):
    root: str = "."


@dataclass(frozen=True)
class RepoMapObservation(ToolObservation):
    root: str
    symbols: tuple = ()
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# apply_patch
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApplyPatchAction(ToolAction):
    path: str
    patch: str


@dataclass(frozen=True)
class ApplyPatchObservation(ToolObservation):
    path: str
    applied: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# git_diff
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GitDiffAction(ToolAction):
    path: str = "."
    ref: Optional[str] = None


@dataclass(frozen=True)
class GitDiffObservation(ToolObservation):
    diff: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# run_command
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunCommandAction(ToolAction):
    argv: tuple
    cwd: str = "."
    timeout_s: int = 30


@dataclass(frozen=True)
class RunCommandObservation(ToolObservation):
    return_code: int
    stdout: str
    stderr: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# run_tests
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunTestsAction(ToolAction):
    test_path: str = "."
    pattern: Optional[str] = None


@dataclass(frozen=True)
class RunTestsObservation(ToolObservation):
    passed: int
    failed: int
    errors: int
    output: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# publish_artifact
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PublishArtifactAction(ToolAction):
    artifact_path: str
    destination: str


@dataclass(frozen=True)
class PublishArtifactObservation(ToolObservation):
    artifact_path: str
    destination: str
    published: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Lookup dicts
# ---------------------------------------------------------------------------

TOOL_ACTION_TYPES: dict = {
    "read_file": ReadFileAction,
    "search": SearchAction,
    "list_dir": ListDirAction,
    "repo_map": RepoMapAction,
    "apply_patch": ApplyPatchAction,
    "git_diff": GitDiffAction,
    "run_command": RunCommandAction,
    "run_tests": RunTestsAction,
    "publish_artifact": PublishArtifactAction,
}

TOOL_OBSERVATION_TYPES: dict = {
    "read_file": ReadFileObservation,
    "search": SearchObservation,
    "list_dir": ListDirObservation,
    "repo_map": RepoMapObservation,
    "apply_patch": ApplyPatchObservation,
    "git_diff": GitDiffObservation,
    "run_command": RunCommandObservation,
    "run_tests": RunTestsObservation,
    "publish_artifact": PublishArtifactObservation,
}

__all__ = [
    "ToolAction",
    "ToolObservation",
    "ReadFileAction",
    "ReadFileObservation",
    "SearchAction",
    "SearchObservation",
    "ListDirAction",
    "ListDirObservation",
    "RepoMapAction",
    "RepoMapObservation",
    "ApplyPatchAction",
    "ApplyPatchObservation",
    "GitDiffAction",
    "GitDiffObservation",
    "RunCommandAction",
    "RunCommandObservation",
    "RunTestsAction",
    "RunTestsObservation",
    "PublishArtifactAction",
    "PublishArtifactObservation",
    "TOOL_ACTION_TYPES",
    "TOOL_OBSERVATION_TYPES",
]
