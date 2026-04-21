"""Tests for framework.domain_branch_first_wave — first-wave domain branch seam."""
import pytest

from framework.domain_branch_first_wave import (
    MEDIA_CONTROL_POLICY,
    MEDIA_LAB_POLICY,
    MEETING_INTELLIGENCE_POLICY,
    FIRST_WAVE_MANIFEST,
    FirstWaveDomainRunner,
)
from framework.domain_branch_contract import DomainBranchPolicy
from framework.task_repetition_harness import RepetitionRunResult
from framework import SAFE_TASK_KINDS


def test_import_ok():
    from framework.domain_branch_first_wave import FIRST_WAVE_MANIFEST, FirstWaveDomainRunner  # noqa: F401


def test_manifest_branch_count():
    assert FIRST_WAVE_MANIFEST.branch_count == 3


def test_manifest_branch_names():
    names = FIRST_WAVE_MANIFEST.branch_names()
    assert "media_control" in names
    assert "media_lab" in names
    assert "meeting_intelligence" in names


def test_media_control_policy_name():
    assert MEDIA_CONTROL_POLICY.branch_name == "media_control"


def test_media_lab_policy_name():
    assert MEDIA_LAB_POLICY.branch_name == "media_lab"


def test_meeting_intelligence_policy_name():
    assert MEETING_INTELLIGENCE_POLICY.branch_name == "meeting_intelligence"


def test_all_policies_require_delegation():
    for policy in FIRST_WAVE_MANIFEST.policies:
        assert policy.requires_runtime_delegation is True


def test_media_control_task_kinds_valid():
    for k in MEDIA_CONTROL_POLICY.task_kinds:
        assert k in SAFE_TASK_KINDS


def test_media_lab_task_kinds_valid():
    for k in MEDIA_LAB_POLICY.task_kinds:
        assert k in SAFE_TASK_KINDS


def test_meeting_intelligence_task_kinds_valid():
    for k in MEETING_INTELLIGENCE_POLICY.task_kinds:
        assert k in SAFE_TASK_KINDS


def test_runner_branch_name():
    runner = FirstWaveDomainRunner()
    assert runner.branch_name() == "first_wave"


def test_runner_run_returns_result():
    runner = FirstWaveDomainRunner()
    result = runner.run(MEDIA_CONTROL_POLICY, dry_run=True, repetitions=2)
    assert isinstance(result, RepetitionRunResult)


def test_runner_run_media_lab():
    runner = FirstWaveDomainRunner()
    result = runner.run(MEDIA_LAB_POLICY, dry_run=True, repetitions=2)
    assert isinstance(result, RepetitionRunResult)


def test_runner_run_meeting_intelligence():
    runner = FirstWaveDomainRunner()
    result = runner.run(MEETING_INTELLIGENCE_POLICY, dry_run=True, repetitions=2)
    assert isinstance(result, RepetitionRunResult)


def test_init_ok_from_framework():
    from framework import FIRST_WAVE_MANIFEST  # noqa: F401
