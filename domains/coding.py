#!/usr/bin/env python3
"""Coding domain: task execution with dual-model workflow."""

import subprocess
import time
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from domains.learning import LearningDomain

DEFAULT_MODEL_CASCADE = [
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "qwen2.5-coder:7b",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "model_pairs.yaml"


@dataclass
class ReviewIssue:
    """A single issue found during code review."""
    severity: str  # "low", "medium", "high"
    category: str  # "style", "bug", "logic_error", etc.
    description: str
    line_context: Optional[str] = None


class CodingDomain:
    """Execute coding tasks with single or dual-model workflow."""

    def __init__(self, framework_runtime=None):
        self.runtime = framework_runtime
        self.repo_root = REPO_ROOT
        self.config = self._load_model_pairs_config()

    def _load_model_pairs_config(self) -> Dict[str, Any]:
        """Load model pairs configuration."""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return yaml.safe_load(f)
        return {
            "pairs": {},
            "default_pair": "fast_accurate",
            "review": {}
        }

    def execute_task(
        self,
        task_description: str,
        files: List[str],
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        max_retries: int = 2,
        allow_dirty: bool = False,
        dual_model: bool = True,
    ) -> Dict[str, Any]:
        """Execute task with optional dual-model workflow.

        Args:
            task_description: What to do
            files: Files to modify
            model: Override model selection
            timeout_seconds: Execution timeout
            max_retries: Fallback retries on failure
            allow_dirty: Skip git clean check
            dual_model: Use writer + reviewer (default True)
        """
        # Validation
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

        # Use dual-model if enabled
        if dual_model:
            return self.execute_task_dual_model(
                task_description, files, model, timeout_seconds, max_retries
            )

        # Single-model fallback
        return self._execute_single_model(
            task_description, files, model, timeout_seconds, max_retries
        )

    def execute_task_dual_model(
        self,
        task_description: str,
        files: List[str],
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Execute with writer model, then review with reviewer model."""
        start_time = time.time()
        pair = self._select_model_pair(task_description, files)

        print(f"\n📝 Phase 1: Writing with {pair['writer']}...")
        write_result = self._execute_with_model(
            pair["writer"], task_description, files, timeout_seconds
        )

        if not write_result["success"]:
            # Record failure
            duration = time.time() - start_time
            try:
                learning = LearningDomain()
                learning.record_execution(
                    task_type="coding",
                    description=task_description,
                    model=pair["writer"],
                    executor="LOCAL_AIDER",
                    success=False,
                    duration_seconds=duration,
                    error_type="write_failed",
                )
            except Exception:
                pass
            return write_result

        print(f"✅ Write phase successful: {write_result['commit_hash'][:8]}")

        # Phase 2: Review
        print(f"🔍 Phase 2: Reviewing with {pair['reviewer']}...")
        review_result = self._review_commit(
            write_result["commit_hash"],
            pair["reviewer"],
            task_description,
            files,
            timeout_seconds,
        )

        # Phase 3: Handle review issues
        if review_result["issues"]:
            print(f"⚠️  Review found {len(review_result['issues'])} issues")
            max_severity = review_result["max_severity"]

            # Determine action based on severity
            if max_severity == "low":
                # Auto-fix low severity
                print("🔧 Auto-fixing low-severity issues...")
                fix_result = self._auto_fix_issues(
                    write_result,
                    review_result,
                    pair["writer"],
                    task_description,
                    files,
                    timeout_seconds,
                )
                duration = time.time() - start_time
                self._record_dual_model_execution(
                    task_description, pair, fix_result["success"], duration, review_result
                )
                return fix_result

            elif max_severity == "medium":
                # Ask user for medium severity
                print("\nReview Issues:")
                for issue in review_result["issues"]:
                    print(f"  [{issue.severity}] {issue.category}: {issue.description}")

                response = input("\nAuto-fix? (y/n): ").strip().lower()
                if response == "y":
                    print("🔧 Auto-fixing medium-severity issues...")
                    fix_result = self._auto_fix_issues(
                        write_result,
                        review_result,
                        pair["writer"],
                        task_description,
                        files,
                        timeout_seconds,
                    )
                    duration = time.time() - start_time
                    self._record_dual_model_execution(
                        task_description, pair, fix_result["success"], duration, review_result
                    )
                    return fix_result
                else:
                    # Keep original
                    duration = time.time() - start_time
                    self._record_dual_model_execution(
                        task_description, pair, True, duration, review_result, user_rejected_fix=True
                    )
                    return write_result

            else:
                # High severity - escalate
                print("\n❌ CRITICAL ISSUES FOUND - ESCALATING")
                print("\nReview Issues:")
                for issue in review_result["issues"]:
                    print(f"  [{issue.severity}] {issue.category}: {issue.description}")

                print("\n⏮️  Rolling back changes...")
                try:
                    subprocess.run(
                        ["git", "reset", "--hard", "HEAD~1"],
                        cwd=self.repo_root,
                        check=True,
                        timeout=10,
                    )
                except Exception as e:
                    print(f"⚠️  Could not rollback: {e}")

                duration = time.time() - start_time
                try:
                    learning = LearningDomain()
                    learning.record_execution(
                        task_type="coding",
                        description=task_description,
                        model=pair["writer"],
                        executor="LOCAL_AIDER",
                        success=False,
                        duration_seconds=duration,
                        error_type="critical_review_issues",
                    )
                except Exception:
                    pass

                return {
                    "success": False,
                    "error": f"Critical issues found during review: {len(review_result['issues'])} issues",
                    "commit_hash": None,
                    "escalate_to": "CLAUDE_CODE",
                    "review_issues": [
                        {
                            "severity": i.severity,
                            "category": i.category,
                            "description": i.description,
                        }
                        for i in review_result["issues"]
                    ],
                }
        else:
            print("✅ Review passed - no issues found")
            duration = time.time() - start_time
            self._record_dual_model_execution(
                task_description, pair, True, duration, review_result
            )
            return write_result

    def _select_model_pair(self, task_description: str, files: List[str]) -> Dict[str, str]:
        """Select writer/reviewer pair based on task complexity."""
        # Simple heuristics for task complexity
        desc_lower = task_description.lower()
        file_count = len(files)

        complexity = "medium"  # default
        if file_count <= 1 and len(task_description) < 50:
            complexity = "simple"
        elif file_count > 3 or len(task_description) > 200:
            complexity = "complex"

        # Find suitable pair
        pairs = self.config.get("pairs", {})
        default_pair_name = self.config.get("default_pair", "fast_accurate")

        for pair_name, pair_config in pairs.items():
            use_for = pair_config.get("use_for", [])
            if complexity in use_for:
                return pair_config

        # Fallback to default
        if default_pair_name in pairs:
            return pairs[default_pair_name]

        # Hardcoded fallback if no config
        return {
            "writer": "qwen2.5-coder:7b",
            "reviewer": "qwen2.5-coder:32b",
        }

    def _review_commit(
        self,
        commit_hash: str,
        reviewer_model: str,
        task_description: str,
        files: List[str],
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        """Review changes in a commit using reviewer model."""
        # Get diff
        try:
            diff_result = subprocess.run(
                ["git", "diff", f"{commit_hash}^..{commit_hash}"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.repo_root,
            )
            diff_text = diff_result.stdout
        except Exception as e:
            return {
                "issues": [],
                "max_severity": "none",
                "error": f"Could not get diff: {e}",
            }

        # Create focused review prompt
        review_prompt = f"""Review the following code changes for potential issues.

Task: {task_description}
Files: {', '.join(files)}

DIFF:
{diff_text[:4000]}

Analyze for:
1. Logic errors or bugs
2. Missing error handling
3. Security issues
4. Incomplete implementations
5. Code style issues

Respond with JSON:
{{
  "issues": [
    {{"severity": "low|medium|high", "category": "style|bug|security|logic|incomplete", "description": "..."}}
  ],
  "summary": "Brief assessment"
}}
"""

        # Send to reviewer model
        cmd = [
            "aider",
            "--no-auto-commits",
            f"--model=ollama/{reviewer_model}",
            "--read=/dev/stdin",
        ]

        try:
            proc = subprocess.run(
                cmd,
                input=review_prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=self.repo_root,
            )

            output = proc.stdout + (proc.stderr or "")

            # Try to extract JSON from output
            try:
                # Look for JSON in output
                import re
                json_match = re.search(r'\{.*"issues".*\}', output, re.DOTALL)
                if json_match:
                    review_data = json.loads(json_match.group())
                    issues = [
                        ReviewIssue(
                            severity=issue.get("severity", "low"),
                            category=issue.get("category", "style"),
                            description=issue.get("description", ""),
                        )
                        for issue in review_data.get("issues", [])
                    ]
                    max_severity = "none"
                    if issues:
                        severity_order = {"low": 0, "medium": 1, "high": 2}
                        max_severity = max(
                            (i.severity for i in issues),
                            key=lambda s: severity_order.get(s, 0),
                        )

                    return {
                        "issues": issues,
                        "max_severity": max_severity,
                        "summary": review_data.get("summary", ""),
                    }
            except Exception:
                pass

            # If no JSON found, assume no issues
            return {
                "issues": [],
                "max_severity": "none",
                "output": output,
            }

        except subprocess.TimeoutExpired:
            return {
                "issues": [],
                "max_severity": "none",
                "error": "Review timeout",
            }
        except Exception as e:
            return {
                "issues": [],
                "max_severity": "none",
                "error": str(e),
            }

    def _auto_fix_issues(
        self,
        original_result: Dict[str, Any],
        review_result: Dict[str, Any],
        writer_model: str,
        task_description: str,
        files: List[str],
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        """Re-run writer model with review feedback."""
        issues_text = "\n".join(
            f"- [{issue.severity}] {issue.category}: {issue.description}"
            for issue in review_result.get("issues", [])
        )

        enhanced_task = f"""{task_description}

IMPORTANT: Fix the following issues found during review:
{issues_text}

Make sure to address all issues and test edge cases."""

        return self._execute_with_model(
            writer_model,
            enhanced_task,
            files,
            timeout_seconds,
        )

    def _execute_single_model(
        self,
        task_description: str,
        files: List[str],
        model: Optional[str],
        timeout_seconds: int,
        max_retries: int,
    ) -> Dict[str, Any]:
        """Execute with single model (fallback from dual-model)."""
        primary_model = model or self._select_model(task_description, files)
        models_to_try = [primary_model]
        for candidate in DEFAULT_MODEL_CASCADE + ["qwen2.5-coder:32b"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error = None
        last_result: Dict[str, Any] = {}
        start_time = time.time()

        for i, current_model in enumerate(models_to_try[: max_retries + 1]):
            result = self._execute_with_model(
                current_model, task_description, files, timeout_seconds
            )
            last_result = result

            if result["success"]:
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

        duration = time.time() - start_time
        error_type = (
            "timeout"
            if "timeout" in str(last_error).lower()
            else "execution_failed"
        )
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

    def _execute_with_model(
        self,
        model: str,
        task_description: str,
        files: list[str],
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Execute task with specific model."""
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
            # Do NOT set AIDER_AUTO_COMMITS=0 — auto-commits are our success signal.
            env["AIDER_NO_SHOW_MODEL_WARNINGS"] = "1"
            env["AIDER_YES"] = "1"
            env["AIDER_DARK_MODE"] = "1"

            # Snapshot HEAD before aider runs — new commit = real file change
            head_before = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5, cwd=self.repo_root,
            ).stdout.strip()

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.repo_root,
                env=env,
            )

            try:
                stdout, stderr = proc.communicate(timeout=timeout_seconds)
                # Combine stdout + stderr so errors are never silently swallowed
                output = stdout
                combined = stdout + ("\n[STDERR]\n" + stderr if stderr.strip() else "")
                for line in stdout.split('\n'):
                    if line.strip():
                        print(line)
                if stderr.strip():
                    print(f"[AIDER STDERR] {stderr[:500]}", flush=True)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    stdout_partial, stderr_partial = proc.communicate(timeout=5)
                except Exception:
                    stdout_partial, stderr_partial = "", ""
                partial_output = stdout_partial or ""
                partial_stderr = stderr_partial or ""
                combined = partial_output + ("\n[STDERR]\n" + partial_stderr if partial_stderr else "")
                result_data["output"] = combined
                raise subprocess.TimeoutExpired(
                    cmd=' '.join(cmd),
                    timeout=timeout_seconds,
                )
            result_data["output"] = combined
            result_data["failure_signatures"] = self._detect_failure_signatures(
                combined, proc.returncode
            )

            if proc.returncode == 0:
                try:
                    commit_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=self.repo_root,
                    )
                    commit_hash = commit_result.stdout.strip()
                    if commit_hash != head_before:
                        # Aider made a real commit — verified success
                        result_data.update({"success": True, "commit_hash": commit_hash})
                    else:
                        # Aider exited 0 but made no commit — model truncated, no change applied
                        result_data.update({
                            "success": False,
                            "error": (
                                "Aider exited 0 but made no git commit. "
                                "Model likely truncated its response (large file under concurrent Ollama load). "
                                "Fix: decompose into smaller new files (<20 lines each)."
                            ),
                        })
                except Exception as exc:
                    result_data.update(
                        {
                            "success": False,
                            "error": f"Could not get commit hash: {exc}",
                        }
                    )
            else:
                # Include stderr in the error message so callers see the real failure
                error_detail = stderr.strip() if stderr.strip() else output.strip()[:200]
                result_data["error"] = (
                    f"Aider exited with code {proc.returncode}"
                    + (f": {error_detail}" if error_detail else "")
                )

        except subprocess.TimeoutExpired:
            result_data["error"] = (
                f"Aider timeout after {timeout_seconds}s — "
                f"model inference is too slow for this timeout. "
                f"Partial output: {result_data.get('output', '')[:300]}"
            )
            result_data["failure_signatures"] = self._detect_failure_signatures(
                result_data["output"], None, timed_out=True
            )
        except FileNotFoundError as exc:
            result_data["error"] = str(exc)
            result_data["failure_signatures"] = ["aider_missing"]
        except Exception as exc:
            result_data["error"] = str(exc)
            result_data["failure_signatures"] = self._detect_failure_signatures(
                result_data["output"], None
            )

        self._save_artifact(model, result_data)
        return result_data

    def _build_aider_command(
        self,
        model: str,
        task_description: str,
        files: list[str],
    ) -> list[str]:
        """Build aider command with context."""
        cmd = [
            "aider",
            # Auto-commits enabled: the only reliable signal that aider applied a change
            # is a new git commit. --no-auto-commits lets aider exit 0 without writing,
            # making success/failure indistinguishable.
            f"--model=ollama/{model}",
            "--yes",
            "--no-show-model-warnings",
            "--no-auto-lint",
            # Disable repo-map: saves one full LLM call per run (~140s for 14b model).
            # With 5 files max, explicit file list is sufficient context.
            "--map-tokens", "0",
        ]

        # Inject repo context — prefer mini summary (~1300 tokens) over full dump (~57k tokens).
        # Full repo_context.txt exceeds the 7b model's 32k window and causes truncation.
        context_chars = 0
        mini_context = self.repo_root / "artifacts" / "repo_context_mini.txt"
        full_context = self.repo_root / "artifacts" / "repo_context.txt"
        if mini_context.exists():
            cmd.append(f"--read={mini_context}")
            context_chars += mini_context.stat().st_size
        elif full_context.exists() and full_context.stat().st_size < 32_000:
            cmd.append(f"--read={full_context}")
            context_chars += full_context.stat().st_size

        # Inject pattern snippets as reference context (budget-aware).
        try:
            from framework.reference_manager import ReferenceManager, CATEGORY_SNIPPETS
            ref_mgr = ReferenceManager(self.repo_root)
            if ref_mgr.snippets_available():
                # Infer category from file paths in the task
                category = "_default"
                desc_lower = task_description.lower()
                for kw, cat in [
                    ("media", "MEDIA"), ("api", "API"), ("data", "DATA"),
                    ("ui", "UI"), ("ops", "OPS"), ("learn", "LEARN"),
                    ("periph", "PERIPH"), ("printer", "PERIPH"), ("niimbot", "PERIPH"),
                    ("serial", "PERIPH"), ("bluetooth", "PERIPH"),
                    ("test", "TEST"), ("core", "CORE"),
                ]:
                    if kw in desc_lower:
                        category = cat
                        break
                # task_description chars + file chars already in context
                used = context_chars + sum(len(f) * 40 for f in files)  # rough file estimate
                for flag in ref_mgr.get_read_flags(
                    category,
                    used_chars=used,
                    task_description=task_description,
                ):
                    cmd.append(flag)
        except Exception:
            pass  # reference system is optional — never block aider

        # Add files first
        cmd.extend(files)

        # Add task as message argument
        cmd.append("--message")
        cmd.append(task_description)

        return cmd

    def _check_git_clean(self) -> bool:
        """Check if git working tree is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.repo_root,
            )
            return not result.stdout.strip()
        except Exception:
            return False

    def _validate_task_bounded(
        self, task_description: str, files: list[str]
    ) -> Tuple[bool, Optional[str]]:
        """Validate task is bounded and executable."""
        if not task_description or not task_description.strip():
            return False, "Task description cannot be empty"
        if not files:
            return False, "Must specify at least one file"
        return True, None

    def _select_model(self, task_description: str, files: list[str]) -> str:
        """Select default model based on task."""
        file_count = len(files)
        if file_count <= 1 and len(task_description) < 50:
            return "qwen2.5-coder:7b"
        elif file_count <= 3:
            return "qwen2.5-coder:14b"
        else:
            return "qwen2.5-coder:32b"

    def _slugify(self, text: str) -> str:
        """Convert text to slug."""
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
        return slug.strip("-")[:50]

    def _detect_failure_signatures(
        self, output: str, returncode: Optional[int], timed_out: bool = False
    ) -> list[str]:
        """Detect failure patterns in output."""
        signatures = []
        if timed_out:
            signatures.append("timeout")
        if returncode and returncode != 0:
            signatures.append(f"exit_code_{returncode}")
        if "error" in output.lower():
            signatures.append("error_in_output")
        if "traceback" in output.lower():
            signatures.append("python_exception")
        return signatures

    def _save_artifact(self, model: str, result_data: Dict[str, Any]) -> None:
        """Save execution artifact."""
        artifact_dir = self.repo_root / "artifacts" / "executions"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        slug = result_data.get("task_slug", "task")
        artifact_file = artifact_dir / f"{timestamp}_{slug}_{model.replace(':', '_')}.json"

        with open(artifact_file, "w") as f:
            json.dump(result_data, f, indent=2)

    def _record_dual_model_execution(
        self,
        task_description: str,
        pair: Dict[str, str],
        success: bool,
        duration: float,
        review_result: Dict[str, Any],
        user_rejected_fix: bool = False,
    ) -> None:
        """Record dual-model execution in learning metrics."""
        try:
            learning = LearningDomain()
            learning.record_execution(
                task_type="coding",
                description=task_description,
                model=pair["writer"],
                executor="LOCAL_AIDER",
                success=success,
                duration_seconds=duration,
                error_type=None if success else "review_issues",
            )
        except Exception:
            pass
