"""First-wave domain branch scaffolds for LAEC1.

Media Control, Media Lab, Meeting Intelligence.
All delegate to TaskRepetitionHarness in dry-run mode.

Inspection gate output:
  SAFE_TASK_KINDS: ['helper_insertion', 'metadata_addition', 'text_replacement']
  RepetitionRunConfig fields: task_kind, num_runs, dry_run, artifact_dir
  make_synthetic_repetition_tasks(task_kind, num_tasks, tmp_dir) -> list[dict]
  TaskRepetitionHarness.run(config: RepetitionRunConfig, tasks: list[dict]) -> RepetitionRunResult
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from framework.domain_branch_contract import (
    DomainBranchManifest,
    DomainBranchPolicy,
    DomainBranchRunner,
)
from framework.task_repetition_harness import TaskRepetitionHarness, RepetitionRunConfig, RepetitionRunResult
from framework.task_repetition_harness import make_synthetic_repetition_tasks

_ISO_NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

MEDIA_CONTROL_POLICY = DomainBranchPolicy(
    branch_name="media_control",
    domain="Media Control",
    task_kinds=("text_replacement", "metadata_addition"),
    description="Media device control and state management tasks",
)

MEDIA_LAB_POLICY = DomainBranchPolicy(
    branch_name="media_lab",
    domain="Media Lab",
    task_kinds=("helper_insertion", "text_replacement"),
    description="Media lab experiment and pipeline tasks",
)

MEETING_INTELLIGENCE_POLICY = DomainBranchPolicy(
    branch_name="meeting_intelligence",
    domain="Meeting Intelligence",
    task_kinds=("text_replacement", "helper_insertion"),
    description="Meeting transcription, summarization, and action item tasks",
)

FIRST_WAVE_MANIFEST = DomainBranchManifest(
    policies=[MEDIA_CONTROL_POLICY, MEDIA_LAB_POLICY, MEETING_INTELLIGENCE_POLICY],
    created_at=_ISO_NOW,
)


class FirstWaveDomainRunner(DomainBranchRunner):
    def branch_name(self) -> str:
        return "first_wave"

    def run(
        self,
        policy: DomainBranchPolicy,
        *,
        dry_run: bool = True,
        repetitions: int = 2,
    ) -> RepetitionRunResult:
        task_kind = policy.task_kinds[0]
        config = RepetitionRunConfig(
            task_kind=task_kind,
            num_runs=repetitions,
            dry_run=dry_run,
            artifact_dir=None,
        )
        with tempfile.TemporaryDirectory() as td:
            tasks = make_synthetic_repetition_tasks(
                task_kind=task_kind,
                num_tasks=repetitions,
                tmp_dir=Path(td),
            )
            harness = TaskRepetitionHarness()
            return harness.run(config, tasks)


__all__ = [
    "MEDIA_CONTROL_POLICY",
    "MEDIA_LAB_POLICY",
    "MEETING_INTELLIGENCE_POLICY",
    "FIRST_WAVE_MANIFEST",
    "FirstWaveDomainRunner",
]
