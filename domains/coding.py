# Coding Domain: Wraps Aider automation and submits coding jobs to framework
# Translates user coding requests into framework JobClass CODING_TASK

from typing import Dict, List, Optional, Any
import yaml
import os
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
