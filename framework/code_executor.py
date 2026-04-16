"""Executor abstraction for Stage 3 code modifications.

This module provides an executor abstraction separating execution planning
(Stage 3 manager) from execution implementation (Claude Code vs Aider).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ExecutionRequest:
    """Request to execute a code modification."""

    message: str
    target: str
    plan_id: str
    stage: str = "stage3"


@dataclass
class ExecutionResult:
    """Result of code execution."""

    success: bool
    executor_name: str
    return_code: int
    started_at: str
    finished_at: str
    events: list[dict[str, Any]]
    classification: str | None = None
    fallback_used: bool = False
    final_tag: str | None = None


class ExecutorBase(ABC):
    """Abstract base for code executors."""

    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a code modification request.

        Args:
            request: ExecutionRequest with message, target, plan_id, stage

        Returns:
            ExecutionResult with success/failure and events
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if executor is available and configured."""
        pass


class ClaudeCodeExecutor(ExecutorBase):
    """Primary executor using Claude Code."""

    def is_available(self) -> bool:
        """Claude Code is always available as primary."""
        return True

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute code modification using Claude Code.

        This implementation handles literal replacements directly in Python,
        and logs changes as "accepted_change" when modifications succeed.
        """
        assert request is not None, "ExecutionRequest must not be None"
        started = datetime.now().isoformat()
        events = []

        target_path = (REPO_ROOT / request.target).resolve()

        # Verify target exists and is readable
        if not target_path.exists():
            events.append({
                "timestamp": datetime.now().isoformat(),
                "executor": "claude_code",
                "status": "failure",
                "tag": "missing_file_ref",
                "note": "path does not exist",
                "plan_id": request.plan_id,
            })
            finished = datetime.now().isoformat()
            return ExecutionResult(
                success=False,
                executor_name="claude_code",
                return_code=1,
                started_at=started,
                finished_at=finished,
                events=events,
                classification="missing_file_ref",
            )

        if not target_path.is_file():
            events.append({
                "timestamp": datetime.now().isoformat(),
                "executor": "claude_code",
                "status": "failure",
                "tag": "missing_file_ref",
                "note": "path exists but is not a file",
                "plan_id": request.plan_id,
            })
            finished = datetime.now().isoformat()
            return ExecutionResult(
                success=False,
                executor_name="claude_code",
                return_code=1,
                started_at=started,
                finished_at=finished,
                events=events,
                classification="missing_file_ref",
            )

        # Read current content
        try:
            content = target_path.read_text(encoding="utf-8")
        except OSError as e:
            events.append({
                "timestamp": datetime.now().isoformat(),
                "executor": "claude_code",
                "status": "failure",
                "tag": "file_read_error",
                "note": str(e)[:100],
                "plan_id": request.plan_id,
            })
            finished = datetime.now().isoformat()
            return ExecutionResult(
                success=False,
                executor_name="claude_code",
                return_code=1,
                started_at=started,
                finished_at=finished,
                events=events,
                classification="repo_unwritable",
            )

        # Parse message for literal replacement pattern
        # Supports multiple formats:
        # 1. "target:: replace exact text 'old' with 'new'" (from stage3_manager validation)
        # 2. "filename::old::new" (simple format)
        # 3. "code_pattern::replacement" (inline format)
        message_text = request.message.strip()
        old_pattern = None
        new_pattern = None

        # First, try to extract from "replace exact text '...' with '...'" format
        literal_match = re.search(r"replace exact text '(.+?)' with '(.+?)'", message_text, re.DOTALL)
        if literal_match:
            old_pattern = literal_match.group(1)
            new_pattern = literal_match.group(2)
        else:
            # Fall back to simple :: parsing
            message_lines = message_text.split("\n")
            for line in message_lines:
                if "::" in line:
                    parts = line.split("::", 2)  # Split on first two "::"
                    if len(parts) == 3 and parts[0].strip() == request.target.split("/")[-1]:
                        # Format: "filename::old::new"
                        old_pattern = parts[1].strip()
                        new_pattern = parts[2].strip()
                        break
                    elif len(parts) == 2 and ("def " in parts[0] or "class " in parts[0]):
                        # Format: "code_pattern::replacement"
                        old_pattern = parts[0].strip()
                        new_pattern = parts[1].strip()
                        break

        # Try simple replacement if patterns were found
        success = False
        _failure_classification = "literal_replace_missing_old"
        modified = content
        if old_pattern and new_pattern:
            if old_pattern in content:
                modified = content.replace(old_pattern, new_pattern, 1)
                success = True
                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "executor": "claude_code",
                    "action": "literal_replace_attempted",
                    "old_len": len(old_pattern),
                    "new_len": len(new_pattern),
                    "plan_id": request.plan_id,
                })
            else:
                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "executor": "claude_code",
                    "status": "failure",
                    "tag": "literal_replace_missing_old",
                    "note": f"pattern not found in {request.target}: old={repr(old_pattern[:40])}",
                    "plan_id": request.plan_id,
                })

        if success:
            # Write modified content
            try:
                target_path.write_text(modified, encoding="utf-8")
                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "executor": "claude_code",
                    "status": "success",
                    "tag": "file_written",
                    "plan_id": request.plan_id,
                })
            except OSError as e:
                success = False
                _failure_classification = "repo_unwritable"
                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "executor": "claude_code",
                    "status": "failure",
                    "tag": "file_write_error",
                    "note": str(e)[:100],
                    "plan_id": request.plan_id,
                })

        finished = datetime.now().isoformat()

        return ExecutionResult(
            success=success,
            executor_name="claude_code",
            return_code=0 if success else 1,
            started_at=started,
            finished_at=finished,
            events=events,
            classification="accepted_change" if success else _failure_classification,
        )


class AiderExecutor(ExecutorBase):
    """Optional fallback executor using Aider via make target."""

    def is_available(self) -> bool:
        """Check if aider-micro-safe make target is available."""
        try:
            result = subprocess.run(
                ["make", "--dry-run", "aider-micro-safe"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute using Aider via make target."""
        assert request is not None, "ExecutionRequest must not be None"
        started = datetime.now().isoformat()

        message_file = self._write_message_file(request.plan_id, request.message)
        try:
            return_code = self._run_aider_micro(message_file, request.target, request.plan_id)
            events = self._load_aider_events(request.plan_id)
            success = return_code == 0
            classification, fallback_used, _, final_tag, _, _, _ = self._classify_from_events(
                events
            )

            finished = datetime.now().isoformat()

            return ExecutionResult(
                success=success,
                executor_name="aider",
                return_code=return_code,
                started_at=started,
                finished_at=finished,
                events=events,
                classification=classification,
                fallback_used=fallback_used,
                final_tag=final_tag,
            )
        finally:
            message_file.unlink(missing_ok=True)

    def _write_message_file(self, plan_id: str, message: str) -> Path:
        """Write message to temporary file."""
        path = Path(tempfile.gettempdir()) / f"stage3_job_{plan_id}.msg"
        path.write_text(message.strip() + "\n", encoding="utf-8")
        return path

    def _run_aider_micro(self, message_file: Path, target: str, plan_id: str) -> int:
        """Run aider-micro-safe make target."""
        env = os.environ.copy()
        env["AIDER_MICRO_STAGE"] = "stage3"
        env["AIDER_MICRO_PLAN_ID"] = plan_id
        cmd = [
            "make",
            "aider-micro-safe",
            f"AIDER_MICRO_MESSAGE_FILE={message_file}",
            f"AIDER_MICRO_FILES={target}",
        ]
        proc = subprocess.run(cmd, env=env)
        return proc.returncode

    def _load_aider_events(self, plan_id: str) -> list[dict]:
        """Load execution events from aider log."""
        event_log = REPO_ROOT / "artifacts" / "micro_runs" / "events.jsonl"
        if not event_log.exists():
            return []
        events: list[dict] = []
        with event_log.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("plan_id") == plan_id:
                    events.append(record)
        return events

    def _classify_from_events(
        self, events: list[dict]
    ) -> tuple[str, bool, bool, str | None, str | None, str | None, int]:
        """Classify result based on events (mirrors stage3_manager logic)."""
        fallback_tags = {"literal_fallback_start", "literal_fallback_applied"}
        failure_class_map = {
            "literal_replace_missing_old": "literal_replace_missing_old",
            "literal_shell_risky": "literal_shell_risky",
            "prompt_contract_rejection": "prompt_contract_rejection",
            "fallback_blocked_running_script": "fallback_blocked_running_script",
            "literal_replace_fallback": "clean_literal_replace_failure",
            "missing_file_ref": "missing_file_ref",
            "missing_anchor": "missing_anchor",
            "comment_scope": "clean_comment_scope_rejection",
            "repo_unwritable": "external_repo_writability_block",
        }

        fallback_used = any(evt.get("tag") in fallback_tags for evt in events)
        final = None
        for evt in reversed(events):
            if evt.get("status") in {"success", "failure"}:
                final = evt
                break

        accepted = False
        classification = "unknown"
        final_tag = None
        final_status = None
        final_note = None
        if final:
            final_status = final.get("status")
            final_tag = final.get("tag") or "completed"
            final_note = final.get("note")
            if final_status == "success":
                accepted = True
                classification = "aider_exit_recovered" if fallback_used else "accepted_change"
            else:
                classification = self._classify_failure(final_tag, fallback_used, failure_class_map)
        else:
            classification = "unknown"

        return (
            classification,
            fallback_used,
            accepted,
            final_tag,
            final_status,
            final_note,
            len(events),
        )

    def _classify_failure(self, final_tag: str | None, fallback_used: bool, mapping: dict) -> str:
        """Classify failure reason."""
        if not final_tag:
            return "other_clean_rejection"

        if final_tag == "aider_exit":
            return "fallback_blocked_running_script"

        if final_tag in {"literal_replace_fallback", "literal_fallback_start", "literal_fallback_applied"}:
            return "clean_literal_replace_failure"

        if final_tag == "no_change":
            return "clean_literal_replace_failure"

        if final_tag == "literal_shell_risky":
            return "literal_shell_risky"

        mapped = mapping.get(final_tag)
        if mapped:
            return mapped

        return "other_clean_rejection"


class ExecutorFactory:
    """Factory for creating executors."""

    _executors: dict[str, type[ExecutorBase]] = {
        "claude_code": ClaudeCodeExecutor,
        "aider": AiderExecutor,
    }

    @classmethod
    def create(cls, executor_name: str | None = None) -> ExecutorBase:
        """Create an executor.

        Args:
            executor_name: "claude_code", "aider", or None for auto-select

        Returns:
            Executor instance

        Raises:
            ValueError: if executor not found
        """
        if executor_name:
            executor_class = cls._executors.get(executor_name)
            if not executor_class:
                raise ValueError(f"Unknown executor: {executor_name}")
            return executor_class()

        # Auto-select: Claude Code primary, Aider fallback
        claude = ClaudeCodeExecutor()
        if claude.is_available():
            return claude
        aider = AiderExecutor()
        if aider.is_available():
            return aider

        # Default to Claude Code (always available)
        return claude

    @classmethod
    def list_available(cls) -> list[tuple[str, bool]]:
        """List all executors and their availability."""
        result = []
        for name, executor_class in cls._executors.items():
            instance = executor_class()
            result.append((name, instance.is_available()))
        return result
