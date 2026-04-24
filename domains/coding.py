from pathlib import Path
from typing import Any, Dict, List, Optional

import json
import os
import subprocess
import time

import yaml

from framework.job_schema import Job, JobClass, JobLifecycle


DEFAULT_MODEL_CASCADE = [
    "qwen2.5-coder:14b",
    "deepseek-coder-v2:latest",
    "qwen2.5-coder:7b",
]

ARTIFACT_ROOT = Path(__file__).resolve().parent.parent / "artifacts" / "aider_runs"


class CodingDomain:
    """
    Domain adapter for code modification tasks.

    Accepts coding requests (file edits, refactors, feature additions) and
    submits them to the framework as CODING_TASK jobs that route to Aider.
    """

    def __init__(self, framework_runtime=None, config: Dict[str, Any] = None):
        """
        Args:
            framework_runtime: Reference to framework worker runtime (optional)
            config: Domain configuration (loads from config/domains.yaml if None)
        """
        self.runtime = framework_runtime

        # Load config from YAML if not provided
        if config is None:
            config = self._load_config()

        self.config = config
        self.enabled = config.get("enabled", True)
        self.model = config.get("parameters", {}).get("model", "qwen2.5-coder:14b")
        self.executor = config.get("parameters", {}).get("executor", "aider")

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """Load CodingDomain config from config/domains.yaml"""
        config_path = Path(__file__).resolve().parent.parent / "config" / "domains.yaml"
        if not config_path.exists():
            return {"enabled": False, "parameters": {}}

        with open(config_path) as f:
            domains_config = yaml.safe_load(f) or {}
            return domains_config.get("domains", {}).get("coding", {})

    def _select_model(self, description: str, files: list[str]) -> str:
        """Select model based on complexity heuristics."""
        lowered = description.lower()

        # Complex tasks: start with the largest available local model.
        if any(kw in lowered for kw in ["complex", "refactor", "redesign", "architecture"]):
            return "qwen2.5-coder:32b"

        # Multi-file or long descriptions: use the strongest default coding model.
        if len(files) > 3 or len(description) > 200:
            return "qwen2.5-coder:14b"

        # Simple tasks: favor the smaller, faster model.
        return "qwen2.5-coder:7b"

    @staticmethod
    def _check_git_clean() -> bool:
        """Verify working tree is clean before execution."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return len(result.stdout.strip()) == 0

    def _validate_task_bounded(self, task_description: str, files: list[str]) -> tuple[bool, str]:
        """Validate task is bounded and safe to execute."""
        if len(files) > 5:
            return False, "Task affects >5 files - too broad, split into smaller tasks"

        dangerous = ["delete all", "remove everything", "rewrite entire", "refactor whole"]
        lowered = task_description.lower()
        for kw in dangerous:
            if kw in lowered:
                return False, f"Task too broad: contains '{kw}'"

        if len(files) > 1:
            for f in files:
                fname = Path(f).name
                if fname not in task_description and f not in task_description:
                    return False, f"Multi-file task must reference each file: '{fname}' not mentioned"

        return True, ""

    @staticmethod
    def _slugify(value: str) -> str:
        slug = []
        for ch in value.strip():
            slug.append(ch if ch.isalnum() or ch in {"-", "_", "."} else "-")
        return "".join(slug).strip("-._") or "task"

    @staticmethod
    def _detect_failure_signatures(output: str, return_code: Optional[int], *, timed_out: bool = False) -> list[str]:
        signatures: list[str] = []
        lowered = output.lower()

        if timed_out:
            signatures.append("timeout")
        if return_code not in (None, 0):
            signatures.append("aider_exit_nonzero")
        if "validation" in lowered and "fail" in lowered:
            signatures.append("validation_failed")
        if "unexpected file" in lowered or "new untracked" in lowered:
            signatures.append("unexpected_file_creation")
        if "no changes" in lowered or "did not edit" in lowered or "no edit" in lowered:
            signatures.append("no_edit_violation")
        if "model" in lowered and ("not found" in lowered or "missing" in lowered or "unavailable" in lowered):
            signatures.append("model_unavailable")
        if "timeout" in lowered and "timeout" not in signatures:
            signatures.append("timeout")

        return list(dict.fromkeys(signatures))

    def _save_artifact(self, model: str, result: Dict[str, Any]) -> None:
        """Save attempt artifacts like bin/aider_local_router.py does."""
        try:
            run_label = result.get("task_slug") or "coding"
            attempt_ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            artifact_dir = ARTIFACT_ROOT / "coding" / f"{attempt_ts}_{run_label}_{os.getpid()}"
            artifact_dir.mkdir(parents=True, exist_ok=True)

            payload = {
                "model": model,
                "success": bool(result.get("success", False)),
                "commit_hash": result.get("commit_hash"),
                "error": result.get("error"),
                "failure_signatures": result.get("failure_signatures", []),
                "output": str(result.get("output", ""))[:1000],
                "timeout_seconds": result.get("timeout_seconds"),
                "timestamp": int(time.time()),
            }
            (artifact_dir / "result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            result["artifact_dir"] = str(artifact_dir)
        except Exception:
            # Artifact capture must never break task execution.
            return

    def _execute_with_model(
        self,
        model: str,
        task_description: str,
        files: list[str],
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Execute task with specific model (existing subprocess logic)."""
        repo_root = Path(__file__).resolve().parent.parent
        cmd = [
            "aider",
            "--model",
            f"ollama/{model}",
            "--yes",
            "--no-auto-commits",
            "--message",
            task_description,
        ]

        for file_path in files:
            cmd.extend(["--file", file_path])

        result_data: Dict[str, Any] = {
            "success": False,
            "commit_hash": None,
            "output": "",
            "error": None,
            "failure_signatures": [],
            "timeout_seconds": timeout_seconds,
            "task_slug": self._slugify(task_description),
            "model": model,
            "model_used": model,
        }

        try:
            env = os.environ.copy()
            env["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"
            env["AIDER_AUTO_COMMITS"] = "0"

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout_seconds,
                cwd=repo_root,
                env=env,
            )

            output = (proc.stdout or "") + (proc.stderr or "")
            result_data["output"] = output
            result_data["failure_signatures"] = self._detect_failure_signatures(output, proc.returncode)

            if proc.returncode == 0:
                try:
                    commit_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=repo_root,
                    )
                    commit_hash = commit_result.stdout.strip()
                    result_data.update(
                        {
                            "success": True,
                            "commit_hash": commit_hash,
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    result_data.update(
                        {
                            "success": False,
                            "error": f"Could not get commit hash: {exc}",
                        }
                    )
            else:
                result_data["error"] = f"Aider exited with code {proc.returncode}"

        except subprocess.TimeoutExpired:
            result_data["error"] = f"Aider timeout after {timeout_seconds} seconds"
            result_data["failure_signatures"] = self._detect_failure_signatures(
                result_data["output"], None, timed_out=True
            )
        except FileNotFoundError as exc:
            result_data["error"] = str(exc)
            result_data["failure_signatures"] = ["aider_missing"]
        except Exception as exc:  # noqa: BLE001
            result_data["error"] = str(exc)
            result_data["failure_signatures"] = self._detect_failure_signatures(result_data["output"], None)

        self._save_artifact(model, result_data)
        return result_data

    def submit_coding_task(
        self,
        description: str,
        files: Optional[List[str]] = None,
        target_files: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """
        Submit a coding task to the framework.

        Args:
            description: Human-readable task description
            files: Files to read/consider
            target_files: Specific files to modify
            context: Additional metadata (priority, timeout, etc)

        Returns:
            Job object with job_id
        """
        job_data = {
            "description": description,
            "files": files or [],
            "target_files": target_files or [],
            "model": self.model,
            "executor": self.executor,
            **(context or {}),
        }

        job = Job(
            job_class=JobClass.CODING_TASK,
            data=job_data,
            lifecycle=JobLifecycle.PENDING,
        )

        return self.runtime.submit_job(job)

    def submit_aider_edit(
        self,
        message: str,
        files: List[str],
        model: Optional[str] = None,
    ) -> Job:
        """
        Convenience: Submit a direct Aider edit request.

        Args:
            message: Aider instruction message
            files: Files to modify
            model: Override default model

        Returns:
            Job object
        """
        return self.submit_coding_task(
            description=message,
            target_files=files,
            context={"model": model or self.model},
        )

    def execute_task(
        self,
        task_description: str,
        files: List[str],
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Execute with model cascade on failure."""
        if not self._check_git_clean():
            return {
                "success": False,
                "error": "Task validation failed: working tree is not clean",
                "commit_hash": None,
                "model_used": None,
            }

        valid, error = self._validate_task_bounded(task_description, files)
        if not valid:
            return {
                "success": False,
                "error": f"Task validation failed: {error}",
                "commit_hash": None,
                "model_used": None,
            }

        primary_model = model or self._select_model(task_description, files)
        models_to_try = [primary_model]
        for candidate in DEFAULT_MODEL_CASCADE + ["qwen2.5-coder:32b"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error = None
        last_result: Dict[str, Any] = {}
        for i, current_model in enumerate(models_to_try[: max_retries + 1]):
            result = self._execute_with_model(current_model, task_description, files, timeout_seconds)
            last_result = result

            if result["success"]:
                return result

            last_error = result.get("error")
            if i < min(max_retries, len(models_to_try) - 1):
                print(f"⚠️  {current_model} failed, trying next model...")

        return {
            "success": False,
            "error": last_error,
            "commit_hash": None,
            "output": last_result.get("output", ""),
            "failure_signatures": last_result.get("failure_signatures", []),
            "artifact_dir": last_result.get("artifact_dir"),
            "model_used": last_result.get("model"),
        }

    def submit_job(self, task_description: str, files: list, priority: int = 5) -> str:
        """Submit coding task to framework scheduler.

        Args:
            task_description: Task to execute
            files: Files to modify
            priority: 1-10 (10=highest)

        Returns:
            job_id: Framework job identifier
        """
        from framework.job_schema import Job, JobClass, JobPriority, JobAction, WorkTarget

        if not self.runtime:
            raise RuntimeError("CodingDomain requires framework_runtime for job submission")

        repo_root = str(Path(__file__).parent.parent)

        job = Job(
            task_class=JobClass.CODING_TASK,
            priority=JobPriority.P0 if priority >= 8 else (JobPriority.P1 if priority >= 5 else JobPriority.P3),
            target=WorkTarget(repo_root=repo_root, worktree_target="main"),
            action=JobAction.SHELL_COMMAND,
            requested_outputs=["git_commit_hash"],
            allowed_tools_actions=["aider"],
            metadata={
                "description": task_description,
                "files": files,
                "executor": "aider",
                "model": self.model,
            },
        )

        submitted_job = self.runtime.submit_job(job)
        return submitted_job.job_id

    def execute_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a scheduled coding job.

        Called by framework worker. Routes to execute_task().
        """
        from framework.job_schema import JobClass

        if not self.runtime:
            return {"success": False, "error": "No framework runtime available"}

        job = self.runtime.scheduler.get_job(job_id)
        if not job or job.task_class != JobClass.CODING_TASK:
            return {"success": False, "error": "Invalid job"}

        description = job.metadata.get("description", "")
        files = job.metadata.get("files", [])
        return self.execute_task(description, files)
