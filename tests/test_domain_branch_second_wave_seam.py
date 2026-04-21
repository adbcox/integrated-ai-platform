"""Tests for framework.domain_branch_second_wave — second-wave domain branch seam."""
import pytest

from framework.domain_branch_second_wave import (
    ATHLETE_ANALYTICS_POLICY,
    OFFICE_AUTOMATION_POLICY,
    SECOND_WAVE_MANIFEST,
    SecondWaveDomainRunner,
)
from framework.task_repetition_harness import RepetitionRunResult
from framework import SAFE_TASK_KINDS


def test_import_ok():
    from framework.domain_branch_second_wave import SECOND_WAVE_MANIFEST, SecondWaveDomainRunner  # noqa: F401


def test_manifest_branch_count():
    assert SECOND_WAVE_MANIFEST.branch_count == 2


def test_manifest_branch_names():
    names = SECOND_WAVE_MANIFEST.branch_names()
    assert "athlete_analytics" in names
    assert "office_automation" in names


def test_athlete_analytics_policy_name():
    assert ATHLETE_ANALYTICS_POLICY.branch_name == "athlete_analytics"


def test_office_automation_policy_name():
    assert OFFICE_AUTOMATION_POLICY.branch_name == "office_automation"


def test_both_policies_require_delegation():
    for policy in SECOND_WAVE_MANIFEST.policies:
        assert policy.requires_runtime_delegation is True


def test_athlete_analytics_task_kinds_valid():
    for k in ATHLETE_ANALYTICS_POLICY.task_kinds:
        assert k in SAFE_TASK_KINDS


def test_office_automation_task_kinds_valid():
    for k in OFFICE_AUTOMATION_POLICY.task_kinds:
        assert k in SAFE_TASK_KINDS


def test_runner_branch_name():
    runner = SecondWaveDomainRunner()
    assert runner.branch_name() == "second_wave"


def test_runner_run_athlete_analytics():
    runner = SecondWaveDomainRunner()
    result = runner.run(ATHLETE_ANALYTICS_POLICY, dry_run=True, repetitions=2)
    assert isinstance(result, RepetitionRunResult)


def test_runner_run_office_automation():
    runner = SecondWaveDomainRunner()
    result = runner.run(OFFICE_AUTOMATION_POLICY, dry_run=True, repetitions=2)
    assert isinstance(result, RepetitionRunResult)


def test_runner_result_total_runs():
    runner = SecondWaveDomainRunner()
    result = runner.run(ATHLETE_ANALYTICS_POLICY, dry_run=True, repetitions=2)
    assert result.total_runs == 2


def test_first_wave_manifest_still_operational():
    from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST
    assert FIRST_WAVE_MANIFEST.branch_count == 3


def test_init_ok_from_framework():
    from framework import SECOND_WAVE_MANIFEST  # noqa: F401
