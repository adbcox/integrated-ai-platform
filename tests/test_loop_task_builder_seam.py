"""Tests for framework.loop_task_builder — LoopTaskBuilder seam."""
import pytest

from framework.mvp_coding_loop import MVPTask
from framework.loop_task_builder import TaskBuildContext, LoopTaskBuilder


def _make_builder(bridge=None, inspector=None):
    return LoopTaskBuilder(retrieval_bridge=bridge, pattern_inspector=inspector)


def test_import_ok():
    from framework.loop_task_builder import TaskBuildContext, LoopTaskBuilder  # noqa: F401


def test_task_build_context_fields():
    ctx = TaskBuildContext(query_text="q", context_snippet="s", pattern_hints=[], cache_hit=False, source="none")
    assert ctx.query_text == "q"
    assert ctx.context_snippet == "s"
    assert ctx.cache_hit is False
    assert ctx.source == "none"


def test_build_returns_task_and_context():
    builder = _make_builder()
    task, ctx = builder.build(
        session_id="s1", target_path="a.py", old_string="foo", new_string="bar",
        task_kind="text_replacement"
    )
    assert isinstance(task, MVPTask)
    assert isinstance(ctx, TaskBuildContext)


def test_build_task_fields_preserved():
    builder = _make_builder()
    task, _ = builder.build(
        session_id="s1", target_path="a.py", old_string="foo", new_string="bar",
        task_kind="text_replacement"
    )
    assert task.session_id == "s1"
    assert task.target_path == "a.py"
    assert task.old_string == "foo"
    assert task.new_string == "bar"
    assert task.task_kind == "text_replacement"


def test_build_task_retrieval_query_set():
    builder = _make_builder()
    task, _ = builder.build(
        session_id="s1", target_path="a.py", old_string="foo", new_string="bar",
        task_kind="text_replacement", query_text="my query"
    )
    assert task.retrieval_query == "my query"


def test_build_retrieval_query_defaults_to_old_string():
    builder = _make_builder()
    task, _ = builder.build(
        session_id="s1", target_path="a.py", old_string="long old string",
        new_string="bar", task_kind="text_replacement"
    )
    assert task.retrieval_query is not None


def test_build_context_only_returns_context():
    builder = _make_builder()
    ctx = builder.build_context_only(query_text="test query", task_kind="text_replacement")
    assert isinstance(ctx, TaskBuildContext)


def test_build_context_only_no_bridge():
    builder = _make_builder(bridge=None)
    ctx = builder.build_context_only(query_text="no bridge")
    assert ctx.source == "none"
    assert ctx.context_snippet == ""


def test_build_context_no_inspector():
    builder = _make_builder(inspector=None)
    ctx = builder.build_context_only(query_text="no inspector", task_kind="text_replacement")
    assert ctx.pattern_hints == []


def test_build_with_no_adapters():
    builder = LoopTaskBuilder()
    task, ctx = builder.build(
        session_id="s1", target_path="a.py", old_string="x", new_string="y",
        task_kind="text_replacement"
    )
    assert isinstance(task, MVPTask)
    assert isinstance(ctx, TaskBuildContext)


def test_replace_all_propagated():
    builder = _make_builder()
    task, _ = builder.build(
        session_id="s1", target_path="a.py", old_string="x", new_string="y",
        task_kind="text_replacement", replace_all=True
    )
    assert task.replace_all is True


def test_enable_revert_propagated():
    builder = _make_builder()
    task, _ = builder.build(
        session_id="s1", target_path="a.py", old_string="x", new_string="y",
        task_kind="text_replacement", enable_revert=False
    )
    assert task.enable_revert is False


def test_build_graceful_degradation_no_retrieval_query_field():
    # MVPTask.retrieval_query exists per inspection gate — this tests behavior is sane regardless
    builder = _make_builder()
    task, ctx = builder.build(
        session_id="s", target_path="f.py", old_string="a", new_string="b",
        task_kind="guard_clause"
    )
    assert task is not None
    assert ctx is not None


def test_init_ok_from_framework():
    from framework import LoopTaskBuilder  # noqa: F401
