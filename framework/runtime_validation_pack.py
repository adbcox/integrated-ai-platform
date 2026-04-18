"""Phase 1 baseline local runtime validation pack.

Proves the Phase 1 local route works end to end:

1. resolve a model profile through the inference gateway,
2. materialize workspace + artifact roots,
3. run at least one local command through the wrapper,
4. emit normalized inference telemetry,
5. write a complete artifact bundle/report,
6. return success deterministically.

The gateway executor is injectable so this pack can run fully offline
in tests while still representing the real local-route shape.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inference_gateway import (
    ExecutorFn,
    GatewayRequest,
    GatewayResponse,
    InferenceGateway,
)
from .local_command_runner import LocalCommandRunner
from .model_profiles import resolve_profile_for_task_class
from .runtime_artifact_service import RuntimeArtifactService
from .runtime_telemetry_schema import RunBundleManifest, ValidationRecord
from .runtime_workspace_contract import RuntimeWorkspace, build_workspace


DEFAULT_TASK_CLASS = "single_file_edit"
DEFAULT_PROMPT = (
    "Phase 1 baseline validation prompt: describe no changes; confirm "
    "gateway resolves profile, workspace materializes, and a local "
    "command completes successfully."
)
DEFAULT_COMMAND = ["python3", "-c", "print('phase1-local-runtime-ok')"]


@dataclass(frozen=True)
class ValidationPackResult:
    success: bool
    manifest_path: Path
    manifest: RunBundleManifest
    inference: GatewayResponse

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "manifest_path": str(self.manifest_path),
            "manifest": self.manifest.to_dict(),
            "inference": self.inference.to_dict(),
        }


def run_baseline_validation(
    *,
    source_root: Path,
    base_root: Path,
    run_id: str,
    session_id: str,
    task_class: str = DEFAULT_TASK_CLASS,
    prompt: str = DEFAULT_PROMPT,
    command: list[str] | str = DEFAULT_COMMAND,
    executor: ExecutorFn | None = None,
) -> ValidationPackResult:
    """Execute the Phase 1 baseline local runtime validation pack."""
    workspace: RuntimeWorkspace = build_workspace(
        source_root=source_root,
        base_root=base_root,
        run_id=run_id,
        session_id=session_id,
    ).ensure_materialized()

    artifact_service = RuntimeArtifactService(workspace)
    profile = resolve_profile_for_task_class(task_class)

    gateway = InferenceGateway(executor=executor)
    request = GatewayRequest(
        profile_name=profile.profile_name,
        prompt=prompt,
        context={"task_class": task_class, "run_id": run_id},
        requested_by="runtime_validation_pack",
    )
    response = gateway.invoke(request)
    artifact_service.record_inference(response.telemetry)
    artifact_service.record_validation(
        ValidationRecord(
            name="gateway_invocation",
            passed=response.success,
            detail=f"profile={response.profile_name} backend={response.backend}",
        )
    )

    runner = LocalCommandRunner()
    command_telemetry = runner.run(command, cwd=workspace.scratch_root)
    artifact_service.record_command(command_telemetry)
    artifact_service.record_validation(
        ValidationRecord(
            name="local_command",
            passed=command_telemetry.success,
            detail=f"return_code={command_telemetry.return_code}",
        )
    )

    # Materialize a small deterministic side-effect into scratch to
    # prove the workspace contract is live for writes.
    scratch_probe = workspace.scratch_root / "baseline_ok.txt"
    scratch_probe.write_text("phase1-local-runtime-ok\n", encoding="utf-8")
    artifact_service.record_side_effect(scratch_probe)

    overall_success = response.success and command_telemetry.success
    manifest = artifact_service.build_manifest(
        profile_name=profile.profile_name,
        final_outcome="completed" if overall_success else "failed",
        artifact_bundle_ref="run_bundle_manifest.json",
    )
    manifest_path = artifact_service.write_manifest(manifest)

    return ValidationPackResult(
        success=overall_success,
        manifest_path=manifest_path,
        manifest=manifest,
        inference=response,
    )


__all__ = [
    "DEFAULT_COMMAND",
    "DEFAULT_PROMPT",
    "DEFAULT_TASK_CLASS",
    "REQUIRED_PHASE2_RUNTIME_KEYS",
    "REQUIRED_PHASE2_TYPED_TOOLS",
    "ValidationPackResult",
    "assert_phase2_runtime_keys_present",
    "run_baseline_validation",
    "run_phase2_runtime_wire_validation",
    "run_phase2_typed_tool_validation",
]


REQUIRED_PHASE2_RUNTIME_KEYS = frozenset(
    {
        "canonical_session",
        "canonical_jobs",
        "typed_tool_trace",
        "permission_decisions",
        "session_bundle",
        "final_outcome",
    }
)


def assert_phase2_runtime_keys_present(payload: dict) -> None:
    missing = [k for k in REQUIRED_PHASE2_RUNTIME_KEYS if k not in payload]
    if missing:
        raise AssertionError(
            f"phase2 runtime payload missing keys: {sorted(missing)}"
        )


def run_phase2_runtime_wire_validation(
    *,
    allow_run_command: bool,
    tmp_root: Path,
) -> dict:
    """Drive one real WorkerRuntime job end-to-end against tmp paths.

    Exercises both allow_run_command=True and allow_run_command=False
    paths by toggling the ``run_command`` entry in
    ``job.allowed_tools_actions``. Returns the real result payload
    emitted by ``WorkerRuntime._execute_job``.

    Deterministic, offline.
    """
    import queue as _queue
    import threading as _threading

    from .backend_profiles import get_backend_profile
    from .inference_adapter import LocalHeuristicInferenceAdapter
    from .job_schema import (
        EscalationPolicy,
        Job,
        JobAction,
        JobClass,
        JobPriority,
        RetryPolicy,
        ValidationRequirement,
        WorkTarget,
    )
    from .learning_hooks import LearningHooks
    from .permission_engine import PermissionEngine
    from .sandbox import LocalSandboxRunner
    from .state_store import StateStore
    from .worker_runtime import WorkerRuntime
    from .workspace import WorkspaceController

    tmp_root = tmp_root.resolve()
    tmp_root.mkdir(parents=True, exist_ok=True)
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    store = StateStore(artifact_root)
    learning = LearningHooks(
        store=store,
        learning_latest_path=artifact_root / "learning" / "latest.json",
    )
    profile = get_backend_profile("mac_local")
    inference = LocalHeuristicInferenceAdapter(profile=profile)
    workspace_controller = WorkspaceController(artifact_root)
    sandbox_runner = LocalSandboxRunner()
    permission_engine = PermissionEngine()

    allowed_tools = ["run_command", "apply_edit"] if allow_run_command else ["apply_edit"]
    session_id = f"phase2-wire-session-{'allow' if allow_run_command else 'block'}"
    suffix = "allow" if allow_run_command else "block"

    job = Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(repo_root=str(repo_root), worktree_target=str(repo_root)),
        action=JobAction.INFERENCE_AND_SHELL,
        requested_outputs=[],
        allowed_tools_actions=allowed_tools,
        retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=False,
            escalate_on_retry_exhaustion=False,
        ),
        validation_requirements=[ValidationRequirement.EXIT_CODE_ZERO],
        metadata={
            "inference_prompt": "phase2 wire validation",
            "shell_command": "echo phase2-wire-ok",
            "session_id": session_id,
            "objective": "phase2 runtime wire validation",
            "model_profile": "fast",
        },
        job_id=f"phase2-wire-job-{suffix}",
    )

    stop_event = _threading.Event()
    runtime = WorkerRuntime(
        worker_id=f"phase2-wire-worker-{suffix}",
        queue_ref=_queue.PriorityQueue(),
        inference=inference,
        store=store,
        learning=learning,
        stop_event=stop_event,
        context_release_callback=lambda _job: None,
        permission_engine=permission_engine,
        workspace_controller=workspace_controller,
        sandbox_runner=sandbox_runner,
    )

    result = runtime._execute_job(job)
    result_path = store.save_result(job.job_id, result)
    persisted = json.loads(result_path.read_text(encoding="utf-8"))

    result["__persisted"] = persisted
    return result


# ------------------------------------------------------------------ #
# Phase 2 typed tool validation helpers                                #
# ------------------------------------------------------------------ #

import os as _p2_os
import subprocess as _p2_sp
from pathlib import Path as _P2Path

from .tool_action_observation_contract import ToolContractName as _P2TCN

REQUIRED_PHASE2_TYPED_TOOLS = (
    _P2TCN.READ_FILE.value,
    _P2TCN.LIST_DIR.value,
    _P2TCN.GIT_DIFF.value,
    _P2TCN.RUN_TESTS.value,
)


def _p2_init_git_repo(repo_root: _P2Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    env = {
        **_p2_os.environ,
        "GIT_AUTHOR_NAME": "phase2-tool-impl",
        "GIT_AUTHOR_EMAIL": "phase2@example.invalid",
        "GIT_COMMITTER_NAME": "phase2-tool-impl",
        "GIT_COMMITTER_EMAIL": "phase2@example.invalid",
    }
    _p2_sp.run(["git", "init", "-q", "-b", "main", str(repo_root)], check=True, env=env)
    (repo_root / "seed.txt").write_text("phase2-seed-content\n", encoding="utf-8")
    _p2_sp.run(["git", "-C", str(repo_root), "add", "seed.txt"], check=True, env=env)
    _p2_sp.run(["git", "-C", str(repo_root), "commit", "-q", "-m", "seed"], check=True, env=env)
    (repo_root / "seed.txt").write_text("phase2-seed-content\nline-two\n", encoding="utf-8")


def _p2_any_profile_name() -> str:
    from .backend_profiles import BACKEND_PROFILES
    if BACKEND_PROFILES:
        return next(iter(BACKEND_PROFILES))
    return "mac_local"


def run_phase2_typed_tool_validation(
    *,
    allow_all_tools: bool,
    tmp_root: Path,
) -> dict:
    """Drive a real WorkerRuntime job with all four Phase 2 typed tools."""
    import queue as _queue
    import threading as _threading

    from .backend_profiles import get_backend_profile
    from .inference_adapter import LocalHeuristicInferenceAdapter
    from .job_schema import (
        EscalationPolicy,
        Job,
        JobAction,
        JobClass,
        JobPriority,
        RetryPolicy,
        WorkTarget,
    )
    from .learning_hooks import LearningHooks
    from .permission_engine import PermissionEngine
    from .sandbox import LocalSandboxRunner
    from .state_store import StateStore
    from .worker_runtime import WorkerRuntime
    from .workspace import WorkspaceController

    tmp_root = tmp_root.resolve()
    tmp_root.mkdir(parents=True, exist_ok=True)
    artifact_root = tmp_root / "artifacts"
    artifact_root.mkdir(parents=True, exist_ok=True)
    repo_root = tmp_root / "repo"
    work_root = tmp_root / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    _p2_init_git_repo(repo_root)

    probe = work_root / "probe.txt"
    probe.write_text("phase2-typed-tool-probe\nline2\n", encoding="utf-8")

    store = StateStore(artifact_root)
    learning = LearningHooks(
        store=store,
        learning_latest_path=artifact_root / "learning" / "latest.json",
    )
    profile_name = _p2_any_profile_name()
    profile = get_backend_profile(profile_name)
    inference = LocalHeuristicInferenceAdapter(profile=profile)
    workspace_controller = WorkspaceController(artifact_root)
    sandbox_runner = LocalSandboxRunner()
    permission_engine = PermissionEngine()

    if allow_all_tools:
        allowed_tools = ["apply_edit", "run_tests", "run_command", "inference"]
    else:
        allowed_tools = ["inference"]

    suffix = "allow" if allow_all_tools else "block"
    session_id = f"phase2-typed-tool-session-{suffix}"

    phase2_typed_tools = [
        {"contract_name": "read_file", "arguments": {"path": "seed.txt"}},
        {"contract_name": "list_dir", "arguments": {"path": "."}},
        {"contract_name": "git_diff", "arguments": {"ref": "HEAD"}},
        {"contract_name": "run_tests", "arguments": {"command": "python3 -m unittest --help"}},
    ]

    job = Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(repo_root=str(repo_root), worktree_target=str(repo_root)),
        action=JobAction.INFERENCE_AND_SHELL,
        requested_outputs=[],
        allowed_tools_actions=allowed_tools,
        retry_policy=RetryPolicy(retry_budget=0, retry_backoff_seconds=0),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=False,
            escalate_on_retry_exhaustion=False,
        ),
        validation_requirements=[],
        metadata={
            "inference_prompt": "phase2 typed tool validation",
            "shell_command": "echo phase2-typed-tool-ok",
            "session_id": session_id,
            "objective": "phase2 typed tool validation",
            "model_profile": profile_name,
            "phase2_typed_tools": phase2_typed_tools,
        },
        job_id=f"phase2-typed-tool-job-{suffix}",
    )

    stop_event = _threading.Event()
    runtime = WorkerRuntime(
        worker_id=f"phase2-typed-tool-worker-{suffix}",
        queue_ref=_queue.PriorityQueue(),
        inference=inference,
        store=store,
        learning=learning,
        stop_event=stop_event,
        context_release_callback=lambda _job: None,
        permission_engine=permission_engine,
        workspace_controller=workspace_controller,
        sandbox_runner=sandbox_runner,
    )

    return runtime._execute_job(job)
