"""Pytest fixtures for the CAP-P2-CLOSE-1 capability session.

Fixtures construct real framework primitives (StateStore, PermissionEngine,
LocalSandboxRunner, WorkspaceController, WorkerRuntime) against a pytest
``tmp_path`` workspace. No monkey-patching of ``framework.worker_runtime``
methods, ``PermissionEngine.evaluate`` or ``StateStore.append_trace`` is
performed here; only dependency stubs strictly needed for construction are
used (a no-op ``context_release_callback`` and an otherwise-unused queue).
"""

from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.backend_profiles import get_backend_profile  # noqa: E402
from framework.inference_adapter import LocalHeuristicInferenceAdapter  # noqa: E402
from framework.job_schema import (  # noqa: E402
    Job,
    JobAction,
    JobClass,
    JobPriority,
    ValidationRequirement,
    WorkTarget,
)
from framework.learning_hooks import LearningHooks  # noqa: E402
from framework.permission_engine import PermissionEngine  # noqa: E402
from framework.sandbox import LocalSandboxRunner  # noqa: E402
from framework.state_store import StateStore  # noqa: E402
from framework.worker_runtime import WorkerRuntime  # noqa: E402
from framework.workspace import WorkspaceController  # noqa: E402


VICTIM_SOURCE = "def answer() -> int:\n    return 0\n\nEXPECTED = 2\n"
# ``-B`` disables Python bytecode writing. macOS's system Python 3 routes
# ``__pycache__`` entries to ``sys.pycache_prefix`` (a per-user cache
# directory), and the pyc header stores the source mtime at one-second
# resolution. Because the capability test rewrites ``victim.py`` many times
# within the same wall-clock second, a stale pyc could shadow the fresh
# source; disabling bytecode persistence forces each cycle to re-parse the
# file on disk. ``-c`` carries the exact assertion the packet specifies.
VALIDATE_COMMAND = (
    'python3 -B -c "import victim; assert victim.answer() == victim.EXPECTED"'
)


@pytest.fixture
def victim_workspace(tmp_path: Path) -> Path:
    (tmp_path / "victim.py").write_text(VICTIM_SOURCE, encoding="utf-8")
    return tmp_path


@pytest.fixture
def artifact_root(tmp_path: Path) -> Path:
    root = tmp_path / "artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def state_store(artifact_root: Path) -> StateStore:
    return StateStore(artifact_root)


@pytest.fixture
def learning_hooks(state_store: StateStore, artifact_root: Path) -> LearningHooks:
    return LearningHooks(
        store=state_store,
        learning_latest_path=artifact_root / "learning" / "latest.json",
    )


@pytest.fixture
def workspace_controller(artifact_root: Path) -> WorkspaceController:
    return WorkspaceController(artifact_root)


@pytest.fixture
def permission_engine() -> PermissionEngine:
    return PermissionEngine()


@pytest.fixture
def sandbox_runner() -> LocalSandboxRunner:
    return LocalSandboxRunner()


@pytest.fixture
def capability_job(victim_workspace: Path) -> Job:
    return Job(
        task_class=JobClass.VALIDATION_CHECK_EXECUTION,
        priority=JobPriority.P2,
        target=WorkTarget(
            repo_root=str(victim_workspace),
            worktree_target=str(victim_workspace),
        ),
        action=JobAction.INFERENCE_AND_SHELL,
        requested_outputs=[str(victim_workspace / "victim.py")],
        allowed_tools_actions=["run_command", "apply_edit"],
        validation_requirements=[ValidationRequirement.EXIT_CODE_ZERO],
    )


@pytest.fixture
def runtime(
    state_store: StateStore,
    learning_hooks: LearningHooks,
    permission_engine: PermissionEngine,
    workspace_controller: WorkspaceController,
    sandbox_runner: LocalSandboxRunner,
) -> WorkerRuntime:
    profile = get_backend_profile("mac_local")
    return WorkerRuntime(
        worker_id="cap-phase2-worker",
        queue_ref=queue.PriorityQueue(),
        inference=LocalHeuristicInferenceAdapter(profile=profile),
        store=state_store,
        learning=learning_hooks,
        stop_event=threading.Event(),
        context_release_callback=lambda _job: None,
        permission_engine=permission_engine,
        workspace_controller=workspace_controller,
        sandbox_runner=sandbox_runner,
    )
