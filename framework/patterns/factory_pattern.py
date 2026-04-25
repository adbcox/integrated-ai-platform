"""Factory pattern — centralized object creation with config-driven dispatch.

Use when: creating objects whose exact type is determined at runtime by
         configuration or environment (executor selection, model routing).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ExecutorType(Enum):
    LOCAL = "local"
    REMOTE = "remote"
    DRY_RUN = "dry_run"


class Executor(ABC):
    @abstractmethod
    def run(self, task: str) -> str: ...


class LocalExecutor(Executor):
    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, task: str) -> str:
        return f"[{self.model}] {task}"


class RemoteExecutor(Executor):
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def run(self, task: str) -> str:
        return f"[remote:{self.endpoint}] {task}"


class DryRunExecutor(Executor):
    def run(self, task: str) -> str:
        return f"[dry-run] {task}"


@dataclass
class ExecutorConfig:
    executor_type: ExecutorType = ExecutorType.LOCAL
    model: str = "qwen2.5-coder:7b"
    endpoint: str = ""
    dry_run: bool = False


class ExecutorFactory:
    """Create the right executor based on config."""

    @staticmethod
    def create(config: ExecutorConfig) -> Executor:
        if config.dry_run or config.executor_type == ExecutorType.DRY_RUN:
            return DryRunExecutor()
        if config.executor_type == ExecutorType.REMOTE:
            return RemoteExecutor(config.endpoint)
        return LocalExecutor(config.model)

    @staticmethod
    def from_env() -> Executor:
        """Auto-detect best executor from environment."""
        import os
        if os.getenv("DRY_RUN"):
            return DryRunExecutor()
        endpoint = os.getenv("REMOTE_EXECUTOR_URL", "")
        if endpoint:
            return RemoteExecutor(endpoint)
        model = os.getenv("LOCAL_MODEL", "qwen2.5-coder:7b")
        return LocalExecutor(model)


if __name__ == "__main__":
    cfg = ExecutorConfig(executor_type=ExecutorType.LOCAL, model="qwen2.5-coder:14b")
    executor = ExecutorFactory.create(cfg)
    print(executor.run("Add error handling to domains/media.py"))
