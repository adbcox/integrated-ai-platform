from pathlib import Path
from typing import Any, Dict, List, Optional

import json
import os
import re
import subprocess
import time

import yaml

from framework.job_schema import Job, JobClass, JobLifecycle
from domains.learning import LearningDomain


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

        # Check for ambiguous references in multi-file tasks
        if len(files) > 1:
            ambiguous_words = ["this", "that", "it", "the file", "the function", "the class"]
            desc_lower = task_description.lower()

            for word in ambiguous_words:
                if word in desc_lower:
                    return False, f"Ambiguous '{word}' in multi-file task - specify which file/function"

            # Check each file is mentioned
            for f in files:
                fname = Path(f).name
                if fname not in task_description and f not in task_description:
                    return False, f"Multi-file task must reference each file: '{fname}' not mentioned in description"

        dangerous = ["delete all", "remove everything", "rewrite entire", "refactor whole"]
        lowered = task_description.lower()
        for kw in dangerous:
            if kw in lowered:
                return False, f"Task too broad: contains '{kw}'"

        return True, ""

    def _find_related_files(self, files: list[str]) -> list[str]:
        """Find imports/related files for context."""
        repo_root = Path(__file__).resolve().parent.parent
        related: set[str] = set()
        primary = set()
        for file_path in files:
            path = Path(file_path)
            if not path.is_absolute():
                path = repo_root / path
            primary.add(str(path.resolve()))

        for file_path in files:
            path = Path(file_path)
            if not path.is_absolute():
                path = repo_root / path
            if not path.exists() or path.suffix != ".py":
                continue

            try:
                source = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            module_prefix = self._module_prefix_for_path(path, repo_root)
            for line in source.splitlines():
                stripped = line.strip()
                if not (stripped.startswith("from ") or stripped.startswith("import ")):
                    continue

                for module_name in self._extract_import_modules(stripped):
                    for candidate in self._resolve_local_module_paths(module_name, repo_root, module_prefix):
                        candidate_str = str(candidate.resolve())
                        if candidate_str in primary or candidate_str in related:
                            continue
                        related.add(candidate_str)
                        break

        return sorted(related)

    @staticmethod
    def _module_prefix_for_path(path: Path, repo_root: Path) -> str:
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            return ""
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts[:-1])

    @staticmethod
    def _extract_import_modules(line: str) -> list[str]:
        modules: list[str] = []
        if line.startswith("import "):
            payload = line[len("import ") :]
            for item in payload.split(","):
                module = item.strip().split(" as ", 1)[0].strip()
                if module:
                    modules.append(module)
        elif line.startswith("from "):
            match = re.match(r"^from\s+([.\w]+)\s+import\s+", line)
            if match:
                modules.append(match.group(1))
        return modules

    @staticmethod
    def _resolve_local_module_paths(module_name: str, repo_root: Path, module_prefix: str) -> list[Path]:
        candidates: list[Path] = []
        resolved_name = module_name

        if module_name.startswith("."):
            base = module_prefix.split(".") if module_prefix else []
            depth = len(module_name) - len(module_name.lstrip("."))
            rel_parts = base[: max(0, len(base) - depth + 1)]
            remainder = module_name.lstrip(".")
            if remainder:
                rel_parts.extend(remainder.split("."))
            resolved_name = ".".join(part for part in rel_parts if part)
            path_base = repo_root.joinpath(*rel_parts) if rel_parts else None
        else:
            path_base = repo_root.joinpath(*module_name.split("."))

        if path_base is not None:
            candidates.append(path_base.with_suffix(".py"))
            candidates.append(path_base / "__init__.py")

        if resolved_name and resolved_name != module_name:
            alt = repo_root.joinpath(*resolved_name.split("."))
            candidates.append(alt.with_suffix(".py"))
            candidates.append(alt / "__init__.py")

        return [path for path in candidates if path.exists()]

    def _build_aider_command(self, model: str, task: str, files: list[str]) -> list[str]:
        cmd = ["aider", "--model", f"ollama/{model}", "--yes", "--no-auto-commits"]

        for f in files:
            cmd.extend(["--file", f])

        related = self._find_related_files(files)
        for r in related[:3]:
            cmd.extend(["--read", r])

        cmd.extend(["--message", task])
        return cmd

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
        cmd = self._build_aider_command(model, task_description, files)

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
        allow_dirty: bool = False,
    ) -> Dict[str, Any]:
        """Execute with model cascade on failure.

        Args:
            allow_dirty: If True, skip git clean check (used with --force flag)
        """
        if not allow_dirty and not self._check_git_clean():
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
        start_time = time.time()

        for i, current_model in enumerate(models_to_try[: max_retries + 1]):
            result = self._execute_with_model(current_model, task_description, files, timeout_seconds)
            last_result = result

            if result["success"]:
                # Record success in learning domain
                duration = time.time() - start_time
                try:
                    learning = LearningDomain()
                    learning.record_execution(
                        task_type="coding",
                        description=task_description,
                        model=current_model,
                        executor="LOCAL_AIDER",
                        success=True,
                        duration_seconds=duration,
                    )
                except Exception:
                    pass
                return result

            last_error = result.get("error")
            if i < min(max_retries, len(models_to_try) - 1):
                print(f"⚠️  {current_model} failed, trying next model...")

        # Record failure in learning domain
        duration = time.time() - start_time
        error_type = "timeout" if "timeout" in str(last_error).lower() else "execution_failed"
        try:
            learning = LearningDomain()
            learning.record_execution(
                task_type="coding",
                description=task_description,
                model=last_result.get("model", primary_model),
                executor="LOCAL_AIDER",
                success=False,
                duration_seconds=duration,
                error_type=error_type,
            )
        except Exception:
            pass

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
