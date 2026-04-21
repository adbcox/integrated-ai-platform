"""Tests for framework.domain_branch_proof_harness — LAPC1 P9."""
import pytest

from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST, FirstWaveDomainRunner
from framework.domain_branch_second_wave import SECOND_WAVE_MANIFEST, SecondWaveDomainRunner
from framework.domain_branch_proof_harness import (
    BRANCH_VERDICT_DONE,
    BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED,
    BRANCH_VERDICT_BLOCKED,
    BRANCH_PROOF_CRITERIA,
    BranchProofCriterionResult,
    BranchProofResult,
    DomainBranchProofHarness,
)


def test_import_ok():
    from framework.domain_branch_proof_harness import DomainBranchProofHarness, BranchProofResult  # noqa: F401


def test_constants():
    assert BRANCH_VERDICT_DONE == "done"
    assert BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED == "scaffold_complete_product_deferred"
    assert BRANCH_VERDICT_BLOCKED == "blocked"


def test_criteria_tuple_length():
    assert len(BRANCH_PROOF_CRITERIA) == 5


def test_criteria_names():
    assert set(BRANCH_PROOF_CRITERIA) == {
        "policy_validates_task_kinds",
        "requires_runtime_delegation",
        "runner_returns_result",
        "result_total_runs_correct",
        "result_success_positive",
    }


def test_evaluate_returns_branch_proof_result():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    assert isinstance(r, BranchProofResult)


def test_evaluate_exactly_five_criteria():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    assert len(r.criterion_results) == 5
    assert r.criteria_total == 5


def test_evaluate_branch_name_correct():
    h = DomainBranchProofHarness()
    policy = FIRST_WAVE_MANIFEST.policies[0]
    r = h.evaluate(policy, FirstWaveDomainRunner(), repetitions=2)
    assert r.branch_name == policy.branch_name


def test_evaluate_dry_run_scaffold_verdict():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    assert r.verdict == BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED


def test_evaluate_all_criteria_pass():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    assert r.criteria_passed == 5


def test_evaluate_batch_first_wave():
    h = DomainBranchProofHarness()
    results = h.evaluate_batch(FIRST_WAVE_MANIFEST, FirstWaveDomainRunner(), repetitions=2)
    assert len(results) == FIRST_WAVE_MANIFEST.branch_count


def test_evaluate_batch_second_wave():
    h = DomainBranchProofHarness()
    results = h.evaluate_batch(SECOND_WAVE_MANIFEST, SecondWaveDomainRunner(), repetitions=2)
    assert len(results) == SECOND_WAVE_MANIFEST.branch_count


def test_evaluate_batch_all_scaffold_complete():
    h = DomainBranchProofHarness()
    results = h.evaluate_batch(FIRST_WAVE_MANIFEST, FirstWaveDomainRunner(), repetitions=2)
    for r in results:
        assert r.verdict == BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED


def test_to_dict_has_branch_name():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    d = r.to_dict()
    assert "branch_name" in d
    assert "verdict" in d
    assert "criteria_passed" in d
    assert "criteria_total" in d


def test_criterion_result_to_dict():
    h = DomainBranchProofHarness()
    r = h.evaluate(FIRST_WAVE_MANIFEST.policies[0], FirstWaveDomainRunner(), repetitions=2)
    cd = r.criterion_results[0].to_dict()
    assert "criterion" in cd
    assert "passed" in cd
    assert "detail" in cd


def test_second_wave_scaffold_complete():
    h = DomainBranchProofHarness()
    results = h.evaluate_batch(SECOND_WAVE_MANIFEST, SecondWaveDomainRunner(), repetitions=2)
    for r in results:
        assert r.verdict == BRANCH_VERDICT_SCAFFOLD_COMPLETE_PRODUCT_DEFERRED


def test_init_ok_from_framework():
    from framework import DomainBranchProofHarness  # noqa: F401
