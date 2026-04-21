"""Domain branch contract surface for LAEC1.

Shared base for all domain branch wave packets. No domain-specific names here.

Inspection gate output:
  RepetitionRunConfig fields: task_kind, num_runs, dry_run, artifact_dir
  RepetitionRunResult fields: config, records, total_runs, success_count,
    failure_count, started_at, finished_at
  TaskRepetitionHarness.run signature: (self, config: RepetitionRunConfig,
    tasks: list[dict]) -> RepetitionRunResult
  SAFE_TASK_KINDS: ['helper_insertion', 'metadata_addition', 'text_replacement']
  make_synthetic_repetition_tasks signature: (task_kind, num_tasks, tmp_dir)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from framework.task_repetition_harness import RepetitionRunResult
from framework.mvp_coding_loop import SAFE_TASK_KINDS

assert isinstance(SAFE_TASK_KINDS, frozenset), "INTERFACE MISMATCH: SAFE_TASK_KINDS must be frozenset"

DOMAIN_BRANCH_RUNNER_VERSION = "1.0"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class DomainBranchPolicy:
    branch_name: str
    domain: str
    task_kinds: tuple
    requires_runtime_delegation: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        for k in self.task_kinds:
            if k not in SAFE_TASK_KINDS:
                raise ValueError(
                    f"task kind {k!r} not in SAFE_TASK_KINDS ({sorted(SAFE_TASK_KINDS)})"
                )


@dataclass
class DomainBranchManifest:
    policies: list
    manifest_version: str = "1.0"
    created_at: str = field(default_factory=_iso_now)
    branch_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.branch_count = len(self.policies)

    def branch_names(self) -> list:
        return [p.branch_name for p in self.policies]

    def get_policy(self, branch_name: str) -> Optional[DomainBranchPolicy]:
        for p in self.policies:
            if p.branch_name == branch_name:
                return p
        return None

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "manifest_version": self.manifest_version,
            "branch_count": self.branch_count,
            "branch_names": self.branch_names(),
            "created_at": self.created_at,
        }


class DomainBranchRunner:
    def run(
        self,
        policy: DomainBranchPolicy,
        *,
        dry_run: bool = True,
        repetitions: int = 2,
    ) -> RepetitionRunResult:
        raise NotImplementedError

    def branch_name(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        try:
            name = self.branch_name()
        except NotImplementedError:
            name = "abstract"
        return f"DomainBranchRunner(branch={name!r})"


__all__ = [
    "DOMAIN_BRANCH_RUNNER_VERSION",
    "DomainBranchPolicy",
    "DomainBranchManifest",
    "DomainBranchRunner",
]
