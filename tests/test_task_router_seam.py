"""Tests for framework.task_router — model/profile routing seam."""
import pytest
from pathlib import Path

from framework.task_router import RoutingDecision, route_task, route_with_memory_update
from framework.local_memory_store import LocalMemoryStore


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


def test_import_ok():
    from framework.task_router import route_task, RoutingDecision  # noqa: F401


def test_route_task_returns_routing_decision(store):
    decision = route_task("text_replacement", memory_store=store)
    assert isinstance(decision, RoutingDecision)


def test_route_task_ollama_first_with_clean_memory(store):
    decision = route_task("text_replacement", memory_store=store)
    assert decision.backend == "ollama"


def test_route_task_external_false_by_default(store):
    decision = route_task("text_replacement", memory_store=store)
    assert decision.external is False


def test_route_task_escalated_false_with_clean_memory(store):
    decision = route_task("text_replacement", memory_store=store)
    assert decision.escalated is False


def test_route_task_includes_task_class(store):
    decision = route_task("bug_fix", memory_store=store)
    assert decision.task_class == "bug_fix"


def test_route_task_includes_reason(store):
    decision = route_task("helper_insertion", memory_store=store)
    assert isinstance(decision.reason, str)
    assert len(decision.reason) > 0


def test_route_task_profile_name_is_known(store):
    from framework.model_profiles import list_profile_names
    decision = route_task("text_replacement", memory_store=store)
    assert decision.profile_name in list_profile_names()


def test_route_task_escalates_on_high_failure_rate(store):
    # Drive failure rate above threshold for text_replacement
    for _ in range(8):
        store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="test failed")
    for _ in range(2):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="y", new_string="z")
    decision = route_task("text_replacement", memory_store=store)
    # With 80% failure rate (above 0.6 threshold), should escalate or return heavier profile
    # Either escalated=True OR a different profile than 'fast'
    assert decision.escalated is True or decision.profile_name != "fast"


def test_route_task_stays_on_base_with_low_failure_rate(store):
    for _ in range(2):
        store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    for _ in range(8):
        store.record_success(task_kind="text_replacement", target_file="a.py", old_string="y", new_string="z")
    decision = route_task("text_replacement", memory_store=store)
    assert decision.escalated is False


def test_route_task_force_profile_returns_forced(store):
    decision = route_task("text_replacement", memory_store=store, force_profile="hard")
    assert decision.profile_name == "hard"
    assert "forced_profile" in decision.reason


def test_route_task_force_profile_with_high_failure_still_forces(store):
    for _ in range(10):
        store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    decision = route_task("text_replacement", memory_store=store, force_profile="balanced")
    assert decision.profile_name == "balanced"


def test_routing_decision_to_dict(store):
    decision = route_task("text_replacement", memory_store=store)
    d = decision.to_dict()
    assert "profile_name" in d
    assert "backend" in d
    assert "model" in d
    assert "task_class" in d
    assert "reason" in d
    assert "escalated" in d
    assert "external" in d


def test_route_task_no_external_when_not_allowed(store):
    # Even with all local profiles degraded, no external when allow_external=False
    for _ in range(10):
        store.record_failure(task_kind="text_replacement", target_file="f.py", old_string="x", error="err")
    decision = route_task("text_replacement", memory_store=store, allow_external=False)
    assert decision.external is False


def test_route_with_memory_update_same_as_route_task(store):
    d1 = route_task("metadata_addition", memory_store=store)
    d2 = route_with_memory_update("metadata_addition", memory_store=store)
    assert d1.profile_name == d2.profile_name
    assert d1.task_class == d2.task_class


def test_route_task_model_is_non_empty(store):
    decision = route_task("bug_fix", memory_store=store)
    assert decision.model
    assert isinstance(decision.model, str)


def test_route_task_unknown_task_class_falls_back_to_local(store):
    decision = route_task("completely_unknown_task_class_xyz", memory_store=store)
    assert decision.backend == "ollama"
    assert isinstance(decision.profile_name, str)
