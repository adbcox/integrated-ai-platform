"""Second-wave domain branch scaffolds for LAEC1.

Athlete Analytics, Office Automation.
All delegate to TaskRepetitionHarness in dry-run mode.
Mirrors first-wave structure exactly.

Inspection gate output:
  FIRST_WAVE_MANIFEST.branch_names(): ['media_control', 'media_lab', 'meeting_intelligence']
  FirstWaveDomainRunner.run sig: (self, policy, *, dry_run=True, repetitions=2) -> RepetitionRunResult
  SAFE_TASK_KINDS: ['helper_insertion', 'metadata_addition', 'text_replacement']
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
from framework.task_repetition_harness import (
    TaskRepetitionHarness,
    RepetitionRunConfig,
    RepetitionRunResult,
    make_synthetic_repetition_tasks,
)

_ISO_NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

ATHLETE_ANALYTICS_POLICY = DomainBranchPolicy(
    branch_name="athlete_analytics",
    domain="Athlete Analytics",
    task_kinds=("metadata_addition", "helper_insertion"),
    description="Athlete performance data and analytics tasks",
)

OFFICE_AUTOMATION_POLICY = DomainBranchPolicy(
    branch_name="office_automation",
    domain="Office Automation",
    task_kinds=("metadata_addition", "text_replacement"),
    description="Office workflow automation and document processing tasks",
)

SECOND_WAVE_MANIFEST = DomainBranchManifest(
    policies=[ATHLETE_ANALYTICS_POLICY, OFFICE_AUTOMATION_POLICY],
    created_at=_ISO_NOW,
)


class SecondWaveDomainRunner(DomainBranchRunner):
    def branch_name(self) -> str:
        return "second_wave"

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
    "ATHLETE_ANALYTICS_POLICY",
    "OFFICE_AUTOMATION_POLICY",
    "SECOND_WAVE_MANIFEST",
    "SecondWaveDomainRunner",
]
