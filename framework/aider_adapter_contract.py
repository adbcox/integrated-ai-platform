"""Aider-under-runtime adapter contract for LAEC1.

Defines the configuration, policy, request, and artifact contract surfaces.
No implementation code. No subprocess or file-mutation code.

Inspection gate output:
  LocalCommandRunner public methods: ['run']
  AiderPreflightChecker.run_preflight signature: (self) -> AiderPreflightResult
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from framework.local_command_runner import LocalCommandRunner as _LocalCommandRunner  # noqa: F401
from framework.aider_preflight import AiderPreflightChecker as _AiderPreflightChecker  # noqa: F401

assert hasattr(_LocalCommandRunner, "run"), "INTERFACE MISMATCH: LocalCommandRunner.run"
assert hasattr(_AiderPreflightChecker, "run_preflight"), "INTERFACE MISMATCH: AiderPreflightChecker.run_preflight"

_ALLOWED_MODEL_PREFIXES = (
    "ollama/",
    "openai/",
    "anthropic/",
    "qwen",
    "deepseek",
    "llama",
    "mistral",
    "codestral",
)


@dataclass(frozen=True)
class AiderAdapterPolicy:
    ollama_first: bool = True
    max_context_files: int = 4
    allow_remote_models: bool = False
    enforce_clean_tree: bool = True
    dry_run_default: bool = True


DEFAULT_AIDER_POLICY = AiderAdapterPolicy(
    ollama_first=True,
    max_context_files=4,
    allow_remote_models=False,
    enforce_clean_tree=True,
    dry_run_default=True,
)


@dataclass
class AiderAdapterConfig:
    model: str
    target_files: list
    message: str
    policy: AiderAdapterPolicy = field(default_factory=lambda: DEFAULT_AIDER_POLICY)
    dry_run: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.model:
            errors.append("model must be non-empty")
        elif not any(self.model.startswith(p) for p in _ALLOWED_MODEL_PREFIXES):
            errors.append(f"model {self.model!r} does not match any allowed prefix")
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
class AiderAdapterRequest:
    config: AiderAdapterConfig
    session_id: str = ""
    context_snippet: str = ""


@dataclass
class AiderAdapterArtifact:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    dry_run: bool
    model: str
    target_files: list
    session_id: str = ""
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "success": self.success,
            "exit_code": self.exit_code,
            "dry_run": self.dry_run,
            "model": self.model,
            "target_files": list(self.target_files),
            "session_id": self.session_id,
            "artifact_path": self.artifact_path,
        }


__all__ = [
    "AiderAdapterPolicy",
    "AiderAdapterConfig",
    "AiderAdapterRequest",
    "AiderAdapterArtifact",
    "DEFAULT_AIDER_POLICY",
]
