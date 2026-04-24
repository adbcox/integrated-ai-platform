import subprocess
import time

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

        proc = subprocess.Popen(
            cmd,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout_seconds,
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        for line in iter(proc.stdout.readline, ''):
            print(line.strip())  # Stream output to console

        proc.wait()

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
