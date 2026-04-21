"""Optional Codex-under-runtime adapter contract for LAEC1.

Mirrors the Aider adapter contract pattern. Codex is optional by policy.
No implementation code.

Inspection gate output:
  AiderAdapterPolicy fields: ollama_first, max_context_files, allow_remote_models,
    enforce_clean_tree, dry_run_default
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from framework.aider_adapter_contract import AiderAdapterPolicy as _AiderAdapterPolicy  # noqa: F401

assert hasattr(_AiderAdapterPolicy, "ollama_first"), "INTERFACE MISMATCH: AiderAdapterPolicy.ollama_first"

CODEX_DEFER_REASON = (
    "Codex adapter is optional; defer when env-backed availability is absent "
    "or when campaign authorization has not been granted for live execution."
)

_ALLOWED_CODEX_MODELS = (
    "claude-",
    "gpt-4",
    "gpt-3.5",
    "o1",
    "o3",
    "o4",
)


@dataclass(frozen=True)
class CodexAdapterPolicy:
    optional: bool = True
    allow_without_api_key: bool = False
    require_explicit_authorization: bool = True
    dry_run_default: bool = True
    max_context_files: int = 6


DEFAULT_CODEX_POLICY = CodexAdapterPolicy(
    optional=True,
    allow_without_api_key=False,
    require_explicit_authorization=True,
    dry_run_default=True,
    max_context_files=6,
)


@dataclass
class CodexAdapterConfig:
    model: str
    target_files: list
    message: str
    policy: CodexAdapterPolicy = field(default_factory=lambda: DEFAULT_CODEX_POLICY)
    dry_run: bool = True

    def is_defer_candidate(self) -> bool:
        has_anthropic_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
        has_key = has_anthropic_key or has_openai_key
        if not has_key:
            return True
        if not self.model:
            return True
        if not any(self.model.startswith(p) for p in _ALLOWED_CODEX_MODELS):
            return True
        return False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.model:
            errors.append("model must be non-empty")
        elif not any(self.model.startswith(p) for p in _ALLOWED_CODEX_MODELS):
            errors.append(f"model {self.model!r} does not match any allowed Codex prefix")
        if not self.target_files:
            errors.append("target_files must be non-empty")
        if len(self.target_files) > self.policy.max_context_files:
            errors.append(
                f"target_files count {len(self.target_files)} exceeds max {self.policy.max_context_files}"
            )
        if not self.message or not self.message.strip():
            errors.append("message must be non-empty")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0


@dataclass
class CodexAdapterRequest:
    config: CodexAdapterConfig
    session_id: str = ""
    context_snippet: str = ""


@dataclass
class CodexAdapterArtifact:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    dry_run: bool
    deferred: bool
    model: str
    target_files: list
    defer_reason: str = ""
    session_id: str = ""
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "success": self.success,
            "exit_code": self.exit_code,
            "dry_run": self.dry_run,
            "deferred": self.deferred,
            "defer_reason": self.defer_reason,
            "model": self.model,
            "target_files": list(self.target_files),
            "session_id": self.session_id,
            "artifact_path": self.artifact_path,
        }


__all__ = [
    "CodexAdapterPolicy",
    "CodexAdapterConfig",
    "CodexAdapterRequest",
    "CodexAdapterArtifact",
    "CODEX_DEFER_REASON",
    "DEFAULT_CODEX_POLICY",
]
