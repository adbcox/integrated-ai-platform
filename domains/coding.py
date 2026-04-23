# Coding Domain: Wraps Aider automation and submits coding jobs to framework
# Translates user coding requests into framework JobClass CODING_TASK

from typing import Dict, List, Optional, Any
import os
import yaml
from framework.job_schema import Job, JobClass, JobLifecycle


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
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "domains.yaml"
        )
        if not os.path.exists(config_path):
            return {"enabled": False, "parameters": {}}

        with open(config_path) as f:
            domains_config = yaml.safe_load(f) or {}
            return domains_config.get("domains", {}).get("coding", {})

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
    ) -> Dict[str, Any]:
        """
        Execute a coding task directly via Aider.

        Args:
            task_description: Instruction for what to do
            files: Target files to modify
            model: Override default model (qwen2.5-coder:14b)
            timeout_seconds: Max execution time (default 300s)

        Returns:
            {
                'success': bool,
                'commit_hash': str (if successful),
                'output': str,
                'error': str (if failed)
            }
        """
        import subprocess
        import re

        model = model or self.model

        # Build aider command
        cmd = [
            "aider",
            "--model",
            f"ollama/{model}",
            "--message",
            task_description,
            "--auto-commits",
            "--auto-test",
            "--no-show-model-warnings",
        ]

        # Add files
        for file_path in files:
            cmd.extend(["--file", file_path])

        try:
            # Set up environment for Ollama
            env = os.environ.copy()
            env.setdefault("OLLAMA_API_BASE", "http://127.0.0.1:11434")

            # Run aider with timeout, no stdin to prevent hanging
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout_seconds,
                cwd=os.path.dirname(os.path.dirname(__file__)),
                env=env,
            )

            output = result.stdout + result.stderr

            # Get latest commit hash if successful
            if result.returncode == 0:
                try:
                    commit_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=os.path.dirname(os.path.dirname(__file__)),
                    )
                    commit_hash = commit_result.stdout.strip()
                    return {
                        "success": True,
                        "commit_hash": commit_hash,
                        "output": output,
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Could not get commit hash: {str(e)}",
                        "output": output,
                    }
            else:
                return {
                    "success": False,
                    "error": f"Aider exited with code {result.returncode}",
                    "output": output,
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Aider timeout after {timeout_seconds} seconds",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
