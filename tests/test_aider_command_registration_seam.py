"""Tests for AGCC1-P2: aider registration in KNOWN_FRAMEWORK_COMMANDS."""
import pytest

from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS, LocalCommandRunner


def test_import_ok():
    from framework.local_command_runner import KNOWN_FRAMEWORK_COMMANDS  # noqa: F401


def test_aider_present():
    assert "aider" in KNOWN_FRAMEWORK_COMMANDS


def test_aider_exactly_once():
    keys = list(KNOWN_FRAMEWORK_COMMANDS.keys())
    assert keys.count("aider") == 1


def test_aider_value_nonempty():
    assert KNOWN_FRAMEWORK_COMMANDS["aider"]


def test_aider_value_is_str():
    assert isinstance(KNOWN_FRAMEWORK_COMMANDS["aider"], str)


def test_existing_check_preserved():
    assert "check" in KNOWN_FRAMEWORK_COMMANDS


def test_existing_quick_preserved():
    assert "quick" in KNOWN_FRAMEWORK_COMMANDS


def test_existing_test_offline_preserved():
    assert "test_offline" in KNOWN_FRAMEWORK_COMMANDS


def test_total_count_at_least_four():
    assert len(KNOWN_FRAMEWORK_COMMANDS) >= 4


def test_all_values_nonempty_strings():
    for k, v in KNOWN_FRAMEWORK_COMMANDS.items():
        assert isinstance(v, str) and v, f"command {k!r} has invalid value {v!r}"


def test_dict_is_str_str():
    for k, v in KNOWN_FRAMEWORK_COMMANDS.items():
        assert isinstance(k, str)
        assert isinstance(v, str)


def test_aider_command_not_empty_argv():
    argv = KNOWN_FRAMEWORK_COMMANDS["aider"]
    assert len(argv.split()) >= 1


def test_local_command_runner_instantiates():
    r = LocalCommandRunner()
    assert r is not None


def test_known_commands_is_dict():
    assert isinstance(KNOWN_FRAMEWORK_COMMANDS, dict)
