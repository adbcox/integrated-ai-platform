"""DomainBranchProofHarness — LAPC1 P9.

Generic five-criterion proof harness for any domain branch.
Inspection gate confirmed:
  DomainBranchPolicy fields: branch_name, domain, task_kinds, requires_runtime_delegation, description
  RepetitionRunResult fields: config, records, total_runs, success_count, failure_count, started_at, finished_at
  TaskRepetitionHarness.run: (self, config, tasks) -> RepetitionRunResult
  SAFE_TASK_KINDS: frozenset({'helper_insertion', 'metadata_addition', 'text_replacement'})
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from framework.domain_branch_contract import (
    DomainBranchPolicy as _DomainBranchPolicy,
    DomainBranchManifest as _DomainBranchManifest,
    DomainBranchRunner as _DomainBranchRunner,
)
from framework.task_repetition_harness import (
    TaskRepetitionHarness as _TaskRepetitionHarness,
    RepetitionRunConfig as _RepetitionRunConfig,
    RepetitionRunResult as _RepetitionRunResult,
    make_synthetic_repetition_tasks as _make_synthetic_repetition_tasks,
)
from framework.mvp_coding_loop import SAFE_TASK_KINDS as _SAFE_TASK_KINDS

assert "branch_name" in _DomainBranchPolicy.__dataclass_fields__, "INTERFACE MISMATCH: DomainBranchPolicy.branch_name"
assert "task_kinds" in _DomainBranchPolicy.__dataclass_fields__, "INTERFACE MISMATCH: DomainBranchPolicy.task_kinds"
assert "requires_runtime_delegation" in _DomainBranchPolicy.__dataclass_fields__, "INTERFACE MISMATCH: DomainBranchPolicy.requires_runtime_delegation"
assert "total_runs" in _RepetitionRunResult.__dataclass_fields__, "INTERFACE MISMATCH: RepetitionRunResult.total_runs"
assert "success_count" in _RepetitionRunResult.__dataclass_fields__, "INTERFACE MISMATCH: RepetitionRunResult.success_count"
assert hasattr(_TaskRepetitionHarness, "run"), "INTERFACE MISMATCH: TaskRepetitionHarness.run"

BRANCH_VERDICT_DONE = "done"
BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED = "scaffold_complete_product_deferred"
BRANCH_VERDICT_BLOCKED = "blocked"

BRANCH_PROOF_CRITERIA = (
    "policy_validates_task_kinds",
    "requires_runtime_delegation",
    "runner_returns_result",
    "result_total_runs_correct",
    "result_success_positive",
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class BranchProofCriterionResult:
    criterion: str
    passed: bool
    detail: str

    def to_dict(self) -> dict:
        return {
            "criterion": self.criterion,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass
class BranchProofResult:
    branch_name: str
    verdict: str
    criterion_results: list
    criteria_passed: int
    criteria_total: int
    evaluated_at: str

    def to_dict(self) -> dict:
        return {
            "branch_name": self.branch_name,
            "verdict": self.verdict,
            "criteria_passed": self.criteria_passed,
            "criteria_total": self.criteria_total,
            "evaluated_at": self.evaluated_at,
            "criterion_results": [c.to_dict() for c in self.criterion_results],
        }


class DomainBranchProofHarness:

    def evaluate(
        self,
        policy: _DomainBranchPolicy,
        runner: _DomainBranchRunner,
        *,
        repetitions: int = 2,
    ) -> BranchProofResult:
        criteria = []

        # Criterion 1: policy_validates_task_kinds
        try:
            for k in policy.task_kinds:
                assert k in _SAFE_TASK_KINDS, f"task kind {k!r} not in SAFE_TASK_KINDS"
            c1_passed = True
            c1_detail = f"task_kinds={list(policy.task_kinds)} all in SAFE_TASK_KINDS"
        except (AssertionError, ValueError) as exc:
            c1_passed = False
            c1_detail = str(exc)
        criteria.append(BranchProofCriterionResult(
            criterion="policy_validates_task_kinds",
            passed=c1_passed,
            detail=c1_detail,
        ))

        # Criterion 2: requires_runtime_delegation
        c2_passed = bool(policy.requires_runtime_delegation)
        criteria.append(BranchProofCriterionResult(
            criterion="requires_runtime_delegation",
            passed=c2_passed,
            detail=f"requires_runtime_delegation={policy.requires_runtime_delegation}",
        ))

        # Criterion 3: runner_returns_result
        run_result = None
        try:
            run_result = runner.run(policy, dry_run=True, repetitions=repetitions)
            c3_passed = isinstance(run_result, _RepetitionRunResult)
            c3_detail = f"runner.run returned {type(run_result).__name__}"
        except Exception as exc:
            c3_passed = False
            c3_detail = f"exception: {exc}"
        criteria.append(BranchProofCriterionResult(
            criterion="runner_returns_result",
            passed=c3_passed,
            detail=c3_detail,
        ))

        # Criterion 4: result_total_runs_correct
        if run_result is not None and c3_passed:
            c4_passed = (run_result.total_runs == repetitions)
            c4_detail = f"total_runs={run_result.total_runs} expected={repetitions}"
        else:
            c4_passed = False
            c4_detail = "no result to check"
        criteria.append(BranchProofCriterionResult(
            criterion="result_total_runs_correct",
            passed=c4_passed,
            detail=c4_detail,
        ))

        # Criterion 5: result_success_positive
        if run_result is not None and c3_passed:
            c5_passed = (run_result.success_count > 0)
            c5_detail = f"success_count={run_result.success_count}"
        else:
            c5_passed = False
            c5_detail = "no result to check"
        criteria.append(BranchProofCriterionResult(
            criterion="result_success_positive",
            passed=c5_passed,
            detail=c5_detail,
        ))

        criteria_passed = sum(1 for c in criteria if c.passed)

        # done is not reachable with dry-run synthetic tasks only
        if criteria_passed == 5:
            verdict = BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED
        else:
            verdict = BRANCH_VERDICT_BLOCKED

        return BranchProofResult(
            branch_name=policy.branch_name,
            verdict=verdict,
            criterion_results=criteria,
            criteria_passed=criteria_passed,
            criteria_total=5,
            evaluated_at=_iso_now(),
        )

    def evaluate_batch(
        self,
        manifest: _DomainBranchManifest,
        runner: _DomainBranchRunner,
        *,
        repetitions: int = 2,
    ) -> list:
        return [self.evaluate(policy, runner, repetitions=repetitions) for policy in manifest.policies]


__all__ = [
    "BRANCH_VERDICT_DONE",
    "BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED",
    "BRANCH_VERDICT_BLOCKED",
    "BRANCH_PROOF_CRITERIA",
    "BranchProofCriterionResult",
    "BranchProofResult",
    "DomainBranchProofHarness",
]
