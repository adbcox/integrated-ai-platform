"""Tests for framework.task_prompt_pack — task-class prompt pack seam."""
import pytest

from framework.task_prompt_pack import (
    SUPPORTED_TASK_CLASSES,
    PromptPack,
    get_prompt_pack,
    render_prompt,
)


def test_supported_task_classes_contains_expected():
    expected = {"text_replacement", "helper_insertion", "metadata_addition", "bug_fix", "narrow_test_update"}
    assert expected == set(SUPPORTED_TASK_CLASSES)


def test_get_prompt_pack_returns_prompt_pack_instance():
    pack = get_prompt_pack("text_replacement")
    assert isinstance(pack, PromptPack)


def test_get_prompt_pack_all_supported_classes():
    for tc in SUPPORTED_TASK_CLASSES:
        pack = get_prompt_pack(tc)
        assert pack.task_class == tc


def test_get_prompt_pack_unknown_raises_key_error():
    with pytest.raises(KeyError, match="unknown_class"):
        get_prompt_pack("unknown_class")


def test_render_includes_task_class():
    result = render_prompt(
        "text_replacement",
        target_file="framework/foo.py",
        file_content="x = 1\n",
        old_string="x = 1",
        new_string_hint="x = 2",
    )
    assert "text_replacement" in result


def test_render_includes_file_path():
    result = render_prompt(
        "helper_insertion",
        target_file="framework/bar.py",
        file_content="def foo(): pass\n",
        old_string="def foo(): pass",
    )
    assert "framework/bar.py" in result


def test_render_includes_file_content():
    content = "def my_func():\n    return 42\n"
    result = render_prompt(
        "bug_fix",
        target_file="framework/x.py",
        file_content=content,
        old_string="return 42",
        new_string_hint="return 43",
    )
    assert content in result


def test_render_includes_old_string():
    result = render_prompt(
        "text_replacement",
        target_file="f.py",
        file_content="VERSION = '1.0'\n",
        old_string="VERSION = '1.0'",
        new_string_hint="VERSION = '2.0'",
    )
    assert "VERSION = '1.0'" in result


def test_render_includes_new_string_hint():
    result = render_prompt(
        "text_replacement",
        target_file="f.py",
        file_content="VERSION = '1.0'\n",
        old_string="VERSION = '1.0'",
        new_string_hint="VERSION = '2.0'",
    )
    assert "VERSION = '2.0'" in result


def test_render_includes_context_snippet_when_provided():
    result = render_prompt(
        "metadata_addition",
        target_file="f.py",
        file_content="# top\n",
        old_string="# top",
        context_snippet="framework/relevant.py: HelperClass, helper_fn",
    )
    assert "framework/relevant.py" in result


def test_render_omits_context_section_when_empty():
    result = render_prompt(
        "text_replacement",
        target_file="f.py",
        file_content="x = 1\n",
        old_string="x = 1",
        context_snippet="",
    )
    assert "[CONTEXT]" not in result


def test_render_includes_extra_instructions():
    result = render_prompt(
        "narrow_test_update",
        target_file="tests/test_foo.py",
        file_content="def test_a(): pass\n",
        extra_instructions="Preserve the test function name exactly.",
    )
    assert "Preserve the test function name exactly." in result


def test_render_includes_output_format_section():
    result = render_prompt(
        "bug_fix",
        target_file="f.py",
        file_content="return None\n",
        old_string="return None",
    )
    assert "[OUTPUT FORMAT]" in result


def test_render_returns_string():
    result = render_prompt(
        "helper_insertion",
        target_file="f.py",
        file_content="pass\n",
    )
    assert isinstance(result, str)
    assert len(result) > 50


def test_prompt_pack_render_method_matches_render_prompt():
    pack = get_prompt_pack("metadata_addition")
    via_pack = pack.render(
        target_file="f.py",
        file_content="# module\n",
        old_string="# module",
        new_string_hint="# module\n# version: 1",
    )
    via_fn = render_prompt(
        "metadata_addition",
        target_file="f.py",
        file_content="# module\n",
        old_string="# module",
        new_string_hint="# module\n# version: 1",
    )
    assert via_pack == via_fn


def test_each_pack_has_non_empty_system_prompt():
    for tc in SUPPORTED_TASK_CLASSES:
        pack = get_prompt_pack(tc)
        assert pack.system_prompt.strip(), f"Empty system_prompt for {tc}"


def test_each_pack_has_non_empty_task_template():
    for tc in SUPPORTED_TASK_CLASSES:
        pack = get_prompt_pack(tc)
        assert pack.task_template.strip(), f"Empty task_template for {tc}"


def test_bug_fix_pack_system_prompt_mentions_minimal_change():
    pack = get_prompt_pack("bug_fix")
    assert "minimal" in pack.system_prompt.lower()


def test_narrow_test_update_pack_mentions_scope():
    pack = get_prompt_pack("narrow_test_update")
    assert "narrowly" in pack.system_prompt.lower() or "narrow" in pack.task_template.lower()
