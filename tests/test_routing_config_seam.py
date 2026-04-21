"""Tests for framework.routing_config and routing_config integration in task_router."""
import json
import pytest
from pathlib import Path

from framework.routing_config import (
    DEFAULT_ROUTING_CONFIG,
    RoutingConfig,
    TaskRoutingOverride,
    load_routing_config,
    save_routing_config,
)
from framework.task_router import route_task
from framework.local_memory_store import LocalMemoryStore


@pytest.fixture
def store(tmp_path):
    return LocalMemoryStore(memory_dir=tmp_path / "memory")


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "routing_config.json"


def test_import_ok():
    from framework.routing_config import RoutingConfig, load_routing_config  # noqa: F401


def test_default_config_global_threshold():
    assert DEFAULT_ROUTING_CONFIG.global_threshold == 0.6


def test_threshold_for_no_override():
    config = RoutingConfig(global_threshold=0.5)
    assert config.threshold_for("text_replacement") == 0.5


def test_threshold_for_with_override():
    config = RoutingConfig(
        overrides=[TaskRoutingOverride(task_class="text_replacement", degraded_failure_rate_threshold=0.4)],
        global_threshold=0.6,
    )
    assert config.threshold_for("text_replacement") == 0.4


def test_threshold_for_falls_back_to_global():
    config = RoutingConfig(
        overrides=[TaskRoutingOverride(task_class="bug_fix", degraded_failure_rate_threshold=0.4)],
        global_threshold=0.7,
    )
    assert config.threshold_for("text_replacement") == 0.7


def test_to_dict_keys():
    config = RoutingConfig()
    d = config.to_dict()
    assert "schema_version" in d
    assert "global_threshold" in d
    assert "overrides" in d


def test_save_dry_run_no_file(config_path):
    config = RoutingConfig()
    result = save_routing_config(config, path=config_path, dry_run=True)
    assert result is None
    assert not config_path.exists()


def test_save_writes_file(config_path):
    config = RoutingConfig()
    result = save_routing_config(config, path=config_path, dry_run=False)
    assert result is not None
    assert config_path.exists()


def test_save_json_valid(config_path):
    config = RoutingConfig(global_threshold=0.55)
    save_routing_config(config, path=config_path, dry_run=False)
    data = json.loads(config_path.read_text())
    assert data["global_threshold"] == 0.55


def test_load_missing_path_returns_default(tmp_path):
    config = load_routing_config(tmp_path / "nonexistent.json")
    assert config.global_threshold == DEFAULT_ROUTING_CONFIG.global_threshold


def test_load_round_trip(config_path):
    original = RoutingConfig(
        overrides=[TaskRoutingOverride(task_class="bug_fix", degraded_failure_rate_threshold=0.45)],
        global_threshold=0.7,
    )
    save_routing_config(original, path=config_path, dry_run=False)
    loaded = load_routing_config(config_path)
    assert loaded.global_threshold == 0.7
    assert loaded.threshold_for("bug_fix") == 0.45


def test_route_task_accepts_routing_config(store):
    config = RoutingConfig(global_threshold=0.6)
    result = route_task("text_replacement", memory_store=store, routing_config=config)
    assert result is not None


def test_route_task_default_behavior_unchanged(store):
    result_default = route_task("text_replacement", memory_store=store)
    result_explicit = route_task("text_replacement", memory_store=store, routing_config=DEFAULT_ROUTING_CONFIG)
    assert result_default.profile_name == result_explicit.profile_name


def test_task_routing_override_fields():
    override = TaskRoutingOverride(task_class="bug_fix", degraded_failure_rate_threshold=0.4)
    assert override.task_class == "bug_fix"
    assert override.degraded_failure_rate_threshold == 0.4


def test_multiple_overrides_each_resolved(tmp_path):
    config = RoutingConfig(
        overrides=[
            TaskRoutingOverride(task_class="text_replacement", degraded_failure_rate_threshold=0.3),
            TaskRoutingOverride(task_class="bug_fix", degraded_failure_rate_threshold=0.5),
        ],
        global_threshold=0.6,
    )
    assert config.threshold_for("text_replacement") == 0.3
    assert config.threshold_for("bug_fix") == 0.5
    assert config.threshold_for("other") == 0.6


def test_route_task_routing_config_none_uses_default(store):
    result = route_task("text_replacement", memory_store=store, routing_config=None)
    assert result is not None
    assert result.task_class == "text_replacement"
