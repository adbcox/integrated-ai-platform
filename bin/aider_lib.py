#!/usr/bin/env python3
"""Shared helpers for the high-throughput Aider automation flow."""
from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Sequence

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "aider_task_classes.json"


@dataclass(frozen=True)
class FileSpec:
    path: str
    action: str = "modify"

    @property
    def normalized(self) -> str:
        return self.path.strip()


DOC_EXTENSIONS = (".md", ".rst", ".txt")
SHELL_EXTENSIONS = (".sh",)


def load_task_classes() -> dict:
    if not CONFIG_PATH.exists():  # pragma: no cover - guard for misconfigured envs
        raise FileNotFoundError(f"Task class config missing: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def parse_file_spec(spec: str) -> FileSpec:
    if ":" in spec:
        path, action = spec.split(":", 1)
    else:
        path, action = spec, "modify"
    path = path.strip()
    if not path:
        raise ValueError("File spec must include a path")
    action = (action.strip() or "modify").lower()
    return FileSpec(path=path, action=action)


def file_roots(paths: Iterable[str]) -> list[str]:
    roots: set[str] = set()
    for path in paths:
        parts = path.split("/", 1)
        roots.add(parts[0])
    return sorted(roots)


def is_doc_file(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("docs/") or lowered.endswith(DOC_EXTENSIONS)


def is_shell_file(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith(SHELL_EXTENSIONS) or lowered.startswith("shell/")


def enforce_class_limits(files: Sequence[FileSpec], class_cfg: dict):
    max_files = class_cfg.get("max_files", 3)
    if len(files) > max_files:
        raise ValueError(f"files supplied ({len(files)}) exceed class budget ({max_files})")

    requires_docs = class_cfg.get("requires_doc_only", False)
    requires_shell = class_cfg.get("requires_shell_only", False)
    for spec in files:
        path = spec.normalized
        if requires_docs and not is_doc_file(path):
            raise ValueError(f"Class requires doc files only, but '{path}' is not doc-scoped")
        if requires_shell and not is_shell_file(path):
            raise ValueError(f"Class requires shell files only, but '{path}' is not shell-scoped")

    roots = file_roots(spec.normalized for spec in files)
    root_limit = class_cfg.get("max_roots")
    if root_limit and len(roots) > root_limit:
        raise ValueError(
            f"Class '{class_cfg}' allows up to {root_limit} root directories, got {len(roots)}: {', '.join(roots)}"
        )


def ensure_paths_exist(files: Sequence[FileSpec]):
    for spec in files:
        path = BASE_DIR / spec.normalized
        action = spec.action
        if action in {"add", "new", "create", "touch"}:
            continue
        if not path.exists():
            raise FileNotFoundError(f"Target file '{spec.normalized}' does not exist; mark as add/new if intentional")


def matches_any_glob(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def describe_make_command(class_name: str, name: str, objective: str, files: Sequence[str]) -> str:
    file_arg = " ".join(files)
    target = class_name.replace("_", "-")
    return (
        f"make aider-{target} AIDER_NAME=\"{name}\" "
        f"AIDER_OBJECTIVE=\"{objective}\" AIDER_FILES=\"{file_arg}\""
    )


def normalize_paths(files: Sequence[FileSpec]) -> list[str]:
    return [spec.normalized for spec in files]


def classify_roots(files: Sequence[FileSpec]) -> dict:
    roots = file_roots(spec.normalized for spec in files)
    return {
        "roots": roots,
        "count": len(roots),
    }


def forbid_patterns(files: Sequence[FileSpec], globs: Sequence[str]) -> list[str]:
    violations = []
    for spec in files:
        if matches_any_glob(spec.normalized, globs):
            violations.append(spec.normalized)
    return violations


def fnmatch_any(paths: Iterable[str], patterns: Sequence[str]) -> int:
    score = 0
    for path in paths:
        for pattern in patterns:
            if fnmatch(path, pattern):
                score += 1
                break
    return score

