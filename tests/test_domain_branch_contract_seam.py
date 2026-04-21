"""Tests for framework.domain_branch_contract — domain branch contract seam."""
import json
import pytest

from framework.domain_branch_contract import (
    DOMAIN_BRANCH_RUNNER_VERSION,
    DomainBranchPolicy,
    DomainBranchManifest,
    DomainBranchRunner,
)


def test_import_ok():
    from framework.domain_branch_contract import DomainBranchPolicy, DomainBranchManifest, DomainBranchRunner  # noqa: F401


def test_runner_version():
    assert DOMAIN_BRANCH_RUNNER_VERSION == "1.0"


def test_valid_policy_constructs():
    p = DomainBranchPolicy(branch_name="test_branch", domain="Test", task_kinds=("text_replacement",))
    assert p.branch_name == "test_branch"
    assert p.requires_runtime_delegation is True


def test_invalid_task_kind_raises():
    with pytest.raises(ValueError, match="not in SAFE_TASK_KINDS"):
        DomainBranchPolicy(branch_name="x", domain="X", task_kinds=("invalid_kind",))


def test_policy_is_frozen():
    p = DomainBranchPolicy(branch_name="x", domain="X", task_kinds=("text_replacement",))
    with pytest.raises((AttributeError, TypeError)):
        p.branch_name = "modified"  # type: ignore


def test_policy_all_safe_kinds():
    from framework import SAFE_TASK_KINDS
    p = DomainBranchPolicy(
        branch_name="x", domain="X",
        task_kinds=tuple(sorted(SAFE_TASK_KINDS))
    )
    assert set(p.task_kinds).issubset(SAFE_TASK_KINDS)


def test_manifest_branch_count():
    p1 = DomainBranchPolicy(branch_name="a", domain="A", task_kinds=("text_replacement",))
    p2 = DomainBranchPolicy(branch_name="b", domain="B", task_kinds=("metadata_addition",))
    manifest = DomainBranchManifest(policies=[p1, p2])
    assert manifest.branch_count == 2


def test_manifest_branch_names():
    p1 = DomainBranchPolicy(branch_name="alpha", domain="A", task_kinds=("text_replacement",))
    p2 = DomainBranchPolicy(branch_name="beta", domain="B", task_kinds=("helper_insertion",))
    manifest = DomainBranchManifest(policies=[p1, p2])
    assert manifest.branch_names() == ["alpha", "beta"]


def test_manifest_get_policy_found():
    p = DomainBranchPolicy(branch_name="target", domain="T", task_kinds=("text_replacement",))
    manifest = DomainBranchManifest(policies=[p])
    found = manifest.get_policy("target")
    assert found is p


def test_manifest_get_policy_missing():
    manifest = DomainBranchManifest(policies=[])
    assert manifest.get_policy("nope") is None


def test_manifest_to_dict_json_safe():
    p = DomainBranchPolicy(branch_name="x", domain="X", task_kinds=("text_replacement",))
    manifest = DomainBranchManifest(policies=[p])
    d = manifest.to_dict()
    json.dumps(d)  # must not raise
    assert d["schema_version"] == 1
    assert d["branch_count"] == 1


def test_runner_run_raises():
    runner = DomainBranchRunner()
    p = DomainBranchPolicy(branch_name="x", domain="X", task_kinds=("text_replacement",))
    with pytest.raises(NotImplementedError):
        runner.run(p)


def test_runner_branch_name_raises():
    runner = DomainBranchRunner()
    with pytest.raises(NotImplementedError):
        runner.branch_name()


def test_init_ok_from_framework():
    from framework import DomainBranchPolicy  # noqa: F401
